"""
Inventory Management and Stock Ledger Application Service for DukaanAI.
Handles variant-level store-aware stock balances, moving average cost (WAC) calculations,
immutable stock ledger movements, physical stock audit workflows, and reconciliation.
Enforces optimistic locking, tenant isolation, and negative stock policies.
"""

from datetime import datetime, timezone
from decimal import Decimal
import math
import uuid
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from backend.app.core.exceptions import (
    BusinessRuleViolation,
    EntityNotFound,
    ResourceConflict,
    ValidationFailure,
)
from backend.app.infrastructure.database.models import (
    Business,
    Category,
    InventoryAdjustment,
    InventoryCountItem,
    InventoryCountSession,
    Product,
    ProductBarcode,
    ProductVariant,
    StockBalance,
    StockMovement,
    Store,
    UnitOfMeasure,
)
from backend.app.schemas.inventory import (
    CompleteCountSessionResponse,
    InventoryCountItemCreate,
    InventoryCountItemResponse,
    InventoryCountSessionCreate,
    InventoryCountSessionResponse,
    InventorySummaryItemResponse,
    InventorySummaryResponse,
    OpeningStockRequest,
    OpeningStockResponse,
    PaginatedStockMovementsResponse,
    ReconciliationReportResponse,
    StockAdjustmentRequest,
    StockAdjustmentResponse,
    StockAdjustmentType,
    StockDetailsResponse,
    StockMovementResponse,
    StockMovementType,
    StockStatus,
)


class InventoryService:
    """Core domain orchestrator for inventory, stock ledger, and store valuation."""

    # -------------------------------------------------------------------------
    # Opening Stock
    # -------------------------------------------------------------------------
    @staticmethod
    def record_opening_stock(
        db: Session,
        business_id: uuid.UUID,
        store_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: OpeningStockRequest,
    ) -> OpeningStockResponse:
        """
        Records the single initial opening stock for a product variant at a store.
        Rejects duplicates if an opening stock movement already exists.
        """
        # Validate Store
        store = db.execute(
            select(Store).where(
                and_(Store.id == store_id, Store.business_id == business_id, Store.is_active.is_(True))
            )
        ).scalar_one_or_none()
        if not store:
            raise EntityNotFound("Store not found or inactive.")

        # Validate Variant
        variant = db.execute(
            select(ProductVariant)
            .join(Product, ProductVariant.product_id == Product.id)
            .where(
                and_(
                    ProductVariant.id == payload.variant_id,
                    Product.business_id == business_id,
                    ProductVariant.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not variant:
            raise EntityNotFound("Product variant not found or inactive.")

        # Check for existing OPENING_STOCK movement
        existing_opening = db.execute(
            select(StockMovement.id).where(
                and_(
                    StockMovement.business_id == business_id,
                    StockMovement.store_id == store_id,
                    StockMovement.variant_id == payload.variant_id,
                    StockMovement.movement_type == StockMovementType.OPENING_STOCK.value,
                )
            )
        ).scalar_one_or_none()
        if existing_opening:
            raise ResourceConflict("Opening stock has already been recorded for this variant at this store.")

        # Lock or initialize StockBalance
        balance = db.execute(
            select(StockBalance)
            .where(
                and_(
                    StockBalance.business_id == business_id,
                    StockBalance.store_id == store_id,
                    StockBalance.variant_id == payload.variant_id,
                )
            )
            .with_for_update()
        ).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        qty = payload.quantity.quantize(Decimal("0.0001"))
        cost = payload.unit_cost.quantize(Decimal("0.0001"))

        if balance is None:
            new_qty = qty
            new_cost = cost
            balance = StockBalance(
                id=uuid.uuid4(),
                business_id=business_id,
                store_id=store_id,
                product_id=variant.product_id,
                variant_id=payload.variant_id,
                current_quantity=new_qty,
                moving_average_cost=new_cost,
                min_stock_level=Decimal("0.0000"),
                reorder_quantity=Decimal("0.0000"),
                version=1,
            )
            db.add(balance)
        else:
            prior_qty = balance.current_quantity
            prior_cost = balance.moving_average_cost
            new_qty = (prior_qty + qty).quantize(Decimal("0.0001"))
            if prior_qty <= Decimal("0.0000"):
                new_cost = cost
            else:
                total_val = (prior_qty * prior_cost) + (qty * cost)
                new_cost = (total_val / new_qty).quantize(Decimal("0.0001"))
            balance.current_quantity = new_qty
            balance.moving_average_cost = new_cost
            balance.version += 1

        # Append immutable StockMovement
        movement_id = uuid.uuid4()
        movement = StockMovement(
            id=movement_id,
            business_id=business_id,
            store_id=store_id,
            product_id=variant.product_id,
            variant_id=payload.variant_id,
            movement_type=StockMovementType.OPENING_STOCK.value,
            quantity_delta=qty,
            uom_id=variant.base_uom_id,
            base_quantity_delta=qty,
            unit_cost_at_movement=cost,
            balance_after_movement=new_qty,
            reference_type="OPENING_STOCK",
            reference_id=movement_id,
            reason="Initial opening stock entry",
            notes=payload.notes,
            idempotency_key=uuid.uuid4(),
            created_by_user_id=user_id,
            occurred_at=now,
            created_at=now,
        )
        db.add(movement)
        balance.last_movement_id = movement.id
        db.flush()

        return OpeningStockResponse(
            movement_id=movement.id,
            variant_id=payload.variant_id,
            store_id=store_id,
            quantity=qty,
            unit_cost=cost,
            current_quantity=balance.current_quantity,
            moving_average_cost=balance.moving_average_cost,
            recorded_at=now,
        )

    # -------------------------------------------------------------------------
    # Stock Adjustments (Manual In, Manual Out, Damage, Expiry, Correction)
    # -------------------------------------------------------------------------
    @staticmethod
    def record_adjustment(
        db: Session,
        business_id: uuid.UUID,
        store_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: StockAdjustmentRequest,
    ) -> StockAdjustmentResponse:
        """
        Records an inventory adjustment, enforcing negative stock policies,
        moving weighted average cost calculations, and creating immutable ledger entries.
        """
        # Validate Store
        store = db.execute(
            select(Store).where(
                and_(Store.id == store_id, Store.business_id == business_id, Store.is_active.is_(True))
            )
        ).scalar_one_or_none()
        if not store:
            raise EntityNotFound("Store not found or inactive.")

        # Validate Business (for negative stock policy)
        business = db.execute(select(Business).where(Business.id == business_id)).scalar_one_or_none()
        if not business:
            raise EntityNotFound("Business not found.")
        negative_policy = getattr(business, "negative_stock_policy", "DISALLOW_NEGATIVE_STOCK")

        # Validate Variant
        variant = db.execute(
            select(ProductVariant)
            .join(Product, ProductVariant.product_id == Product.id)
            .where(
                and_(
                    ProductVariant.id == payload.variant_id,
                    Product.business_id == business_id,
                    ProductVariant.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not variant:
            raise EntityNotFound("Product variant not found or inactive.")

        # Lock StockBalance
        balance = db.execute(
            select(StockBalance)
            .where(
                and_(
                    StockBalance.business_id == business_id,
                    StockBalance.store_id == store_id,
                    StockBalance.variant_id == payload.variant_id,
                )
            )
            .with_for_update()
        ).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        qty = payload.quantity.quantize(Decimal("0.0001"))
        prev_qty = balance.current_quantity if balance else Decimal("0.0000")
        prev_cost = balance.moving_average_cost if balance else (variant.cost_price or Decimal("0.0000"))

        adj_type = payload.adjustment_type
        is_inward = adj_type in (StockAdjustmentType.MANUAL_IN,)

        if is_inward:
            # Inward addition
            delta = qty
            cost = (payload.unit_cost if payload.unit_cost is not None else prev_cost).quantize(Decimal("0.0001"))
            movement_type = StockMovementType.MANUAL_ADJUSTMENT_IN.value

            # Weighted Average Cost Calculation
            new_qty = (prev_qty + delta).quantize(Decimal("0.0001"))
            if prev_qty <= Decimal("0.0000"):
                new_cost = cost
            else:
                total_val = (prev_qty * prev_cost) + (qty * cost)
                new_cost = (total_val / new_qty).quantize(Decimal("0.0001"))
        else:
            # Outward deduction (MANUAL_OUT, DAMAGE, EXPIRY, COUNT_CORRECTION)
            delta = -qty
            cost = prev_cost.quantize(Decimal("0.0001"))
            new_qty = (prev_qty + delta).quantize(Decimal("0.0001"))
            new_cost = prev_cost  # Outward movements relieve stock at current WAC without altering unit cost basis

            if adj_type == StockAdjustmentType.DAMAGE:
                movement_type = StockMovementType.DAMAGE.value
            elif adj_type == StockAdjustmentType.EXPIRY:
                movement_type = StockMovementType.EXPIRY.value
            elif adj_type == StockAdjustmentType.COUNT_CORRECTION:
                movement_type = StockMovementType.AUDIT_ADJUSTMENT.value
            else:
                movement_type = StockMovementType.MANUAL_ADJUSTMENT_OUT.value

            # Check Negative Stock Policy
            if new_qty < Decimal("0.0000") and negative_policy == "DISALLOW_NEGATIVE_STOCK":
                shortfall = abs(new_qty)
                raise BusinessRuleViolation(
                    f"Insufficient stock: requested deduction of {qty} exceeds available balance of {prev_qty} "
                    f"(shortfall of {shortfall}). Negative stock is disallowed for this business."
                )

        # Upsert StockBalance
        if balance is None:
            balance = StockBalance(
                id=uuid.uuid4(),
                business_id=business_id,
                store_id=store_id,
                product_id=variant.product_id,
                variant_id=payload.variant_id,
                current_quantity=new_qty,
                moving_average_cost=new_cost,
                min_stock_level=Decimal("0.0000"),
                reorder_quantity=Decimal("0.0000"),
                version=1,
            )
            db.add(balance)
        else:
            balance.current_quantity = new_qty
            balance.moving_average_cost = new_cost
            balance.version += 1

        adjustment_id = uuid.uuid4()
        movement = StockMovement(
            id=uuid.uuid4(),
            business_id=business_id,
            store_id=store_id,
            product_id=variant.product_id,
            variant_id=payload.variant_id,
            movement_type=movement_type,
            quantity_delta=delta,
            uom_id=variant.base_uom_id,
            base_quantity_delta=delta,
            unit_cost_at_movement=cost,
            balance_after_movement=new_qty,
            reference_type="INVENTORY_ADJUSTMENT",
            reference_id=adjustment_id,
            reason=payload.reason,
            notes=payload.notes,
            idempotency_key=uuid.uuid4(),
            created_by_user_id=user_id,
            occurred_at=now,
            created_at=now,
        )
        db.add(movement)
        balance.last_movement_id = movement.id

        # Record InventoryAdjustment
        adjustment = InventoryAdjustment(
            id=adjustment_id,
            business_id=business_id,
            store_id=store_id,
            product_id=variant.product_id,
            variant_id=payload.variant_id,
            movement_id=movement.id,
            adjustment_type=adj_type.value,
            system_quantity=prev_qty,
            counted_quantity=new_qty,
            variance_quantity=delta,
            reason=payload.reason,
            created_by_user_id=user_id,
            approved_by_user_id=user_id,
        )
        db.add(adjustment)
        db.flush()

        return StockAdjustmentResponse(
            adjustment_id=adjustment.id,
            movement_id=movement.id,
            variant_id=payload.variant_id,
            adjustment_type=adj_type.value,
            quantity=qty,
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            moving_average_cost=new_cost,
            recorded_at=now,
        )

    # -------------------------------------------------------------------------
    # Physical Stock Count Audits
    # -------------------------------------------------------------------------
    @staticmethod
    def create_count_session(
        db: Session,
        business_id: uuid.UUID,
        store_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: InventoryCountSessionCreate,
    ) -> InventoryCountSessionResponse:
        """Creates a new physical stock counting session."""
        store = db.execute(
            select(Store).where(
                and_(Store.id == store_id, Store.business_id == business_id, Store.is_active.is_(True))
            )
        ).scalar_one_or_none()
        if not store:
            raise EntityNotFound("Store not found or inactive.")

        now = datetime.now(timezone.utc)
        session_id = uuid.uuid4()
        session_num = f"COUNT-{now.strftime('%Y%m%d')}-{str(session_id)[:6].upper()}"

        session = InventoryCountSession(
            id=session_id,
            business_id=business_id,
            store_id=store_id,
            conducted_by_user_id=user_id,
            status="OPEN",
            notes=payload.notes,
            started_at=now,
        )
        db.add(session)
        db.flush()

        return InventoryCountSessionResponse(
            id=session.id,
            business_id=session.business_id,
            store_id=session.store_id,
            session_number=session_num,
            status=session.status,
            total_variants_counted=0,
            total_variance_quantity=Decimal("0.0000"),
            total_variance_value=Decimal("0.0000"),
            notes=session.notes,
            created_at=session.started_at,
            completed_at=session.completed_at,
            items=[],
        )

    @staticmethod
    def list_count_sessions(
        db: Session,
        business_id: uuid.UUID,
        store_id: uuid.UUID,
    ) -> list[InventoryCountSessionResponse]:
        """Lists all physical count sessions for a store."""
        sessions = (
            db.execute(
                select(InventoryCountSession)
                .options(selectinload(InventoryCountSession.items))
                .where(
                    and_(
                        InventoryCountSession.business_id == business_id,
                        InventoryCountSession.store_id == store_id,
                    )
                )
                .order_by(InventoryCountSession.started_at.desc())
            )
            .scalars()
            .all()
        )

        results = []
        for s in sessions:
            items_count = len(s.items)
            total_var_qty = sum((item.variance_quantity for item in s.items), Decimal("0.0000"))
            session_num = f"COUNT-{s.started_at.strftime('%Y%m%d')}-{str(s.id)[:6].upper()}"
            results.append(
                InventoryCountSessionResponse(
                    id=s.id,
                    business_id=s.business_id,
                    store_id=s.store_id,
                    session_number=session_num,
                    status=s.status,
                    total_variants_counted=items_count,
                    total_variance_quantity=total_var_qty,
                    total_variance_value=Decimal("0.0000"),
                    notes=s.notes,
                    created_at=s.started_at,
                    completed_at=s.completed_at,
                    items=[],
                )
            )
        return results

    @staticmethod
    def get_count_session(
        db: Session,
        business_id: uuid.UUID,
        store_id: uuid.UUID,
        count_id: uuid.UUID,
    ) -> InventoryCountSessionResponse:
        """Retrieves details of a physical count session and its line items."""
        session = (
            db.execute(
                select(InventoryCountSession)
                .options(selectinload(InventoryCountSession.items))
                .where(
                    and_(
                        InventoryCountSession.id == count_id,
                        InventoryCountSession.business_id == business_id,
                        InventoryCountSession.store_id == store_id,
                    )
                )
            )
            .scalar_one_or_none()
        )
        if not session:
            raise EntityNotFound("Inventory count session not found.")

        item_responses: list[InventoryCountItemResponse] = []
        total_var_qty = Decimal("0.0000")
        total_var_val = Decimal("0.0000")

        for it in session.items:
            variant = db.execute(
                select(ProductVariant)
                .options(selectinload(ProductVariant.product), selectinload(ProductVariant.barcodes))
                .where(ProductVariant.id == it.variant_id)
            ).scalar_one_or_none()

            balance = db.execute(
                select(StockBalance).where(
                    and_(
                        StockBalance.business_id == business_id,
                        StockBalance.store_id == store_id,
                        StockBalance.variant_id == it.variant_id,
                    )
                )
            ).scalar_one_or_none()

            cost = balance.moving_average_cost if balance else (variant.cost_price if variant else Decimal("0.0000"))
            var_val = (it.variance_quantity * cost).quantize(Decimal("0.0001"))

            total_var_qty += it.variance_quantity
            total_var_val += var_val

            barcode = variant.barcodes[0].barcode if (variant and variant.barcodes) else None

            item_responses.append(
                InventoryCountItemResponse(
                    id=it.id,
                    session_id=it.session_id,
                    product_id=it.product_id,
                    variant_id=it.variant_id,
                    product_name=variant.product.name if variant and variant.product else None,
                    variant_name=variant.variant_name if variant else None,
                    sku=variant.sku if variant else None,
                    barcode=barcode,
                    expected_quantity=it.expected_quantity,
                    counted_quantity=it.counted_quantity,
                    variance_quantity=it.variance_quantity,
                    unit_cost=cost,
                    variance_value=var_val,
                    notes=it.notes,
                )
            )

        session_num = f"COUNT-{session.started_at.strftime('%Y%m%d')}-{str(session.id)[:6].upper()}"

        return InventoryCountSessionResponse(
            id=session.id,
            business_id=session.business_id,
            store_id=session.store_id,
            session_number=session_num,
            status=session.status,
            total_variants_counted=len(item_responses),
            total_variance_quantity=total_var_qty,
            total_variance_value=total_var_val,
            notes=session.notes,
            created_at=session.started_at,
            completed_at=session.completed_at,
            items=item_responses,
        )

    @staticmethod
    def add_count_item(
        db: Session,
        business_id: uuid.UUID,
        store_id: uuid.UUID,
        count_id: uuid.UUID,
        payload: InventoryCountItemCreate,
    ) -> InventoryCountItemResponse:
        """Adds or updates a counted item in an open count session."""
        session = db.execute(
            select(InventoryCountSession).where(
                and_(
                    InventoryCountSession.id == count_id,
                    InventoryCountSession.business_id == business_id,
                    InventoryCountSession.store_id == store_id,
                )
            )
        ).scalar_one_or_none()
        if not session:
            raise EntityNotFound("Inventory count session not found.")
        if session.status != "OPEN":
            raise BusinessRuleViolation(f"Cannot record counts against a session in {session.status} status.")

        variant = db.execute(
            select(ProductVariant)
            .options(selectinload(ProductVariant.product), selectinload(ProductVariant.barcodes))
            .where(
                and_(
                    ProductVariant.id == payload.variant_id,
                    ProductVariant.business_id == business_id,
                    ProductVariant.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not variant:
            raise EntityNotFound("Product variant not found or inactive.")

        balance = db.execute(
            select(StockBalance).where(
                and_(
                    StockBalance.business_id == business_id,
                    StockBalance.store_id == store_id,
                    StockBalance.variant_id == payload.variant_id,
                )
            )
        ).scalar_one_or_none()

        expected_qty = balance.current_quantity if balance else Decimal("0.0000")
        cost = balance.moving_average_cost if balance else (variant.cost_price or Decimal("0.0000"))
        counted_qty = payload.counted_quantity.quantize(Decimal("0.0001"))
        variance_qty = (counted_qty - expected_qty).quantize(Decimal("0.0001"))
        var_val = (variance_qty * cost).quantize(Decimal("0.0001"))

        existing_item = db.execute(
            select(InventoryCountItem).where(
                and_(
                    InventoryCountItem.session_id == count_id,
                    InventoryCountItem.variant_id == payload.variant_id,
                )
            )
        ).scalar_one_or_none()

        if existing_item:
            existing_item.counted_quantity = counted_qty
            existing_item.variance_quantity = variance_qty
            existing_item.notes = payload.notes
            item = existing_item
        else:
            item = InventoryCountItem(
                id=uuid.uuid4(),
                business_id=business_id,
                store_id=store_id,
                session_id=count_id,
                product_id=variant.product_id,
                variant_id=payload.variant_id,
                expected_quantity=expected_qty,
                counted_quantity=counted_qty,
                variance_quantity=variance_qty,
                notes=payload.notes,
            )
            db.add(item)

        db.flush()

        barcode = variant.barcodes[0].barcode if (variant and variant.barcodes) else None

        return InventoryCountItemResponse(
            id=item.id,
            session_id=item.session_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            product_name=variant.product.name if variant and variant.product else None,
            variant_name=variant.variant_name if variant else None,
            sku=variant.sku if variant else None,
            barcode=barcode,
            expected_quantity=item.expected_quantity,
            counted_quantity=item.counted_quantity,
            variance_quantity=item.variance_quantity,
            unit_cost=cost,
            variance_value=var_val,
            notes=item.notes,
        )

    @staticmethod
    def complete_count_session(
        db: Session,
        business_id: uuid.UUID,
        store_id: uuid.UUID,
        user_id: uuid.UUID,
        count_id: uuid.UUID,
    ) -> CompleteCountSessionResponse:
        """
        Finalizes an open count session, generates AUDIT_ADJUSTMENT movements
        for all line items with non-zero variance, updates stock balances,
        and transitions the session to COMPLETED.
        """
        session = (
            db.execute(
                select(InventoryCountSession)
                .options(selectinload(InventoryCountSession.items))
                .where(
                    and_(
                        InventoryCountSession.id == count_id,
                        InventoryCountSession.business_id == business_id,
                        InventoryCountSession.store_id == store_id,
                    )
                )
                .with_for_update()
            )
            .scalar_one_or_none()
        )
        if not session:
            raise EntityNotFound("Inventory count session not found.")
        if session.status != "OPEN":
            raise BusinessRuleViolation(f"Cannot complete session in {session.status} status.")

        now = datetime.now(timezone.utc)
        items_adjusted = 0
        total_var_value = Decimal("0.0000")

        for it in session.items:
            if it.variance_quantity == Decimal("0.0000"):
                continue

            balance = db.execute(
                select(StockBalance)
                .where(
                    and_(
                        StockBalance.business_id == business_id,
                        StockBalance.store_id == store_id,
                        StockBalance.variant_id == it.variant_id,
                    )
                )
                .with_for_update()
            ).scalar_one_or_none()

            cost = balance.moving_average_cost if balance else Decimal("0.0000")
            delta = it.variance_quantity
            item_var_val = (delta * cost).quantize(Decimal("0.0001"))
            total_var_value += item_var_val

            if balance is None:
                balance = StockBalance(
                    id=uuid.uuid4(),
                    business_id=business_id,
                    store_id=store_id,
                    product_id=it.product_id,
                    variant_id=it.variant_id,
                    current_quantity=it.counted_quantity,
                    moving_average_cost=cost,
                    min_stock_level=Decimal("0.0000"),
                    reorder_quantity=Decimal("0.0000"),
                    version=1,
                )
                db.add(balance)
            else:
                balance.current_quantity = it.counted_quantity
                balance.version += 1

            variant = db.execute(
                select(ProductVariant).where(ProductVariant.id == it.variant_id)
            ).scalar_one_or_none()
            uom_id = variant.base_uom_id if variant else None

            # Generate AUDIT_ADJUSTMENT movement
            movement_id = uuid.uuid4()
            movement = StockMovement(
                id=movement_id,
                business_id=business_id,
                store_id=store_id,
                product_id=it.product_id,
                variant_id=it.variant_id,
                movement_type=StockMovementType.AUDIT_ADJUSTMENT.value,
                quantity_delta=delta,
                uom_id=uom_id,
                base_quantity_delta=delta,
                unit_cost_at_movement=cost,
                balance_after_movement=it.counted_quantity,
                reference_type="INVENTORY_COUNT_SESSION",
                reference_id=session.id,
                reason=f"Count session: expected {it.expected_quantity}, counted {it.counted_quantity}",
                notes=it.notes,
                idempotency_key=uuid.uuid4(),
                created_by_user_id=user_id,
                occurred_at=now,
                created_at=now,
            )
            db.add(movement)
            balance.last_movement_id = movement.id
            items_adjusted += 1

        session.status = "COMPLETED"
        session.completed_at = now
        db.flush()

        return CompleteCountSessionResponse(
            session_id=session.id,
            status="COMPLETED",
            items_adjusted=items_adjusted,
            total_variance_value=total_var_value,
            completed_at=now,
        )

    # -------------------------------------------------------------------------
    # Inventory Summary & Stock Details
    # -------------------------------------------------------------------------
    @staticmethod
    def get_inventory_summary(
        db: Session,
        business_id: uuid.UUID,
        store_id: uuid.UUID,
        query: str | None = None,
        category_id: uuid.UUID | None = None,
        low_stock_only: bool = False,
        out_of_stock_only: bool = False,
        page: int = 1,
        limit: int = 50,
    ) -> InventorySummaryResponse:
        """
        Retrieves paginated store inventory overview with KPIs:
        total items, total inventory valuation, low stock count, and out of stock count.
        """
        page = max(1, page)
        limit = max(1, min(limit, 200))
        offset = (page - 1) * limit

        base_stmt = (
            select(
                ProductVariant,
                Product,
                UnitOfMeasure,
                Category,
                StockBalance,
            )
            .options(selectinload(ProductVariant.barcodes))
            .join(Product, ProductVariant.product_id == Product.id)
            .join(UnitOfMeasure, ProductVariant.base_uom_id == UnitOfMeasure.id)
            .outerjoin(Category, Product.category_id == Category.id)
            .outerjoin(
                StockBalance,
                and_(
                    StockBalance.variant_id == ProductVariant.id,
                    StockBalance.store_id == store_id,
                    StockBalance.business_id == business_id,
                ),
            )
            .where(
                and_(
                    Product.business_id == business_id,
                    Product.is_active.is_(True),
                    ProductVariant.is_active.is_(True),
                )
            )
        )

        if category_id:
            base_stmt = base_stmt.where(Product.category_id == category_id)

        if query and query.strip():
            clean = f"%{query.strip().lower()}%"
            base_stmt = base_stmt.where(
                or_(
                    func.lower(Product.name).like(clean),
                    func.lower(ProductVariant.variant_name).like(clean),
                    func.lower(ProductVariant.sku).like(clean),
                )
            )

        all_rows = db.execute(base_stmt).all()

        total_items = len(all_rows)
        total_valuation = Decimal("0.0000")
        low_stock_count = 0
        out_of_stock_count = 0

        filtered_items: list[InventorySummaryItemResponse] = []

        for row in all_rows:
            var: ProductVariant = row[0]
            prod: Product = row[1]
            uom: UnitOfMeasure = row[2]
            cat: Category | None = row[3]
            bal: StockBalance | None = row[4]

            qty = bal.current_quantity if bal else Decimal("0.0000")
            min_stock = bal.min_stock_level if bal else Decimal("0.0000")
            reorder_qty = bal.reorder_quantity if bal else Decimal("0.0000")
            cost = bal.moving_average_cost if bal else (var.cost_price or Decimal("0.0000"))
            selling_price = var.selling_price or Decimal("0.0000")
            val = (max(Decimal("0.0000"), qty) * cost).quantize(Decimal("0.0001"))

            total_valuation += val

            if qty <= Decimal("0.0000"):
                status = StockStatus.OUT_OF_STOCK.value
                out_of_stock_count += 1
            elif min_stock > Decimal("0.0000") and qty <= min_stock:
                status = StockStatus.LOW_STOCK.value
                low_stock_count += 1
            else:
                status = StockStatus.IN_STOCK.value

            if out_of_stock_only and status != StockStatus.OUT_OF_STOCK.value:
                continue
            if low_stock_only and status != StockStatus.LOW_STOCK.value:
                continue

            barcode = var.barcodes[0].barcode if var.barcodes else None

            filtered_items.append(
                InventorySummaryItemResponse(
                    variant_id=var.id,
                    product_id=prod.id,
                    product_name=prod.name,
                    variant_name=var.variant_name,
                    sku=var.sku,
                    barcode=barcode,
                    category_name=cat.name if cat else None,
                    current_quantity=qty,
                    uom_name=uom.name,
                    moving_average_cost=cost,
                    selling_price=selling_price,
                    inventory_valuation=val,
                    min_stock_level=min_stock,
                    reorder_quantity=reorder_qty,
                    stock_status=status,
                    last_movement_at=bal.updated_at if bal else None,
                )
            )

        total_filtered = len(filtered_items)
        paginated_items = filtered_items[offset : offset + limit]
        total_pages = math.ceil(total_filtered / limit) if total_filtered > 0 else 1

        return InventorySummaryResponse(
            total_items=total_items,
            total_valuation=total_valuation,
            low_stock_count=low_stock_count,
            out_of_stock_count=out_of_stock_count,
            items=paginated_items,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    @staticmethod
    def get_variant_stock_details(
        db: Session,
        business_id: uuid.UUID,
        store_id: uuid.UUID,
        variant_id: uuid.UUID,
    ) -> StockDetailsResponse:
        """Retrieves comprehensive stock and valuation metrics for a single product variant."""
        row = db.execute(
            select(ProductVariant, Product, UnitOfMeasure, Category, StockBalance)
            .options(selectinload(ProductVariant.barcodes))
            .join(Product, ProductVariant.product_id == Product.id)
            .join(UnitOfMeasure, ProductVariant.base_uom_id == UnitOfMeasure.id)
            .outerjoin(Category, Product.category_id == Category.id)
            .outerjoin(
                StockBalance,
                and_(
                    StockBalance.variant_id == ProductVariant.id,
                    StockBalance.store_id == store_id,
                    StockBalance.business_id == business_id,
                ),
            )
            .where(
                and_(
                    ProductVariant.id == variant_id,
                    Product.business_id == business_id,
                )
            )
        ).first()

        if not row:
            raise EntityNotFound("Product variant not found.")

        var: ProductVariant = row[0]
        prod: Product = row[1]
        uom: UnitOfMeasure = row[2]
        cat: Category | None = row[3]
        bal: StockBalance | None = row[4]

        qty = bal.current_quantity if bal else Decimal("0.0000")
        min_stock = bal.min_stock_level if bal else Decimal("0.0000")
        reorder_qty = bal.reorder_quantity if bal else Decimal("0.0000")
        cost = bal.moving_average_cost if bal else (var.cost_price or Decimal("0.0000"))
        selling_price = var.selling_price or Decimal("0.0000")
        mrp = var.mrp or Decimal("0.0000")
        val = (max(Decimal("0.0000"), qty) * cost).quantize(Decimal("0.0001"))

        if qty <= Decimal("0.0000"):
            status = StockStatus.OUT_OF_STOCK.value
        elif min_stock > Decimal("0.0000") and qty <= min_stock:
            status = StockStatus.LOW_STOCK.value
        else:
            status = StockStatus.IN_STOCK.value

        has_opening = (
            db.execute(
                select(StockMovement.id).where(
                    and_(
                        StockMovement.business_id == business_id,
                        StockMovement.store_id == store_id,
                        StockMovement.variant_id == variant_id,
                        StockMovement.movement_type == StockMovementType.OPENING_STOCK.value,
                    )
                )
            ).scalar_one_or_none()
            is not None
        )

        barcode = var.barcodes[0].barcode if var.barcodes else None

        return StockDetailsResponse(
            variant_id=var.id,
            product_id=prod.id,
            product_name=prod.name,
            variant_name=var.variant_name,
            sku=var.sku,
            barcode=barcode,
            category_name=cat.name if cat else None,
            current_quantity=qty,
            uom_name=uom.name,
            moving_average_cost=cost,
            selling_price=selling_price,
            mrp=mrp,
            inventory_valuation=val,
            min_stock_level=min_stock,
            reorder_quantity=reorder_qty,
            stock_status=status,
            has_opening_stock=has_opening,
        )

    # -------------------------------------------------------------------------
    # Stock Movements Ledger
    # -------------------------------------------------------------------------
    @staticmethod
    def list_stock_movements(
        db: Session,
        business_id: uuid.UUID,
        store_id: uuid.UUID,
        variant_id: uuid.UUID | None = None,
        movement_type: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> PaginatedStockMovementsResponse:
        """Retrieves paginated audit log of immutable stock ledger movements."""
        page = max(1, page)
        limit = max(1, min(limit, 200))
        offset = (page - 1) * limit

        stmt = select(StockMovement).where(
            and_(
                StockMovement.business_id == business_id,
                StockMovement.store_id == store_id,
            )
        )

        if variant_id:
            stmt = stmt.where(StockMovement.variant_id == variant_id)
        if movement_type:
            stmt = stmt.where(StockMovement.movement_type == movement_type)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar() or 0

        movements = (
            db.execute(
                stmt.order_by(StockMovement.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            .scalars()
            .all()
        )

        items = [
            StockMovementResponse(
                id=m.id,
                business_id=m.business_id,
                store_id=m.store_id,
                variant_id=m.variant_id,
                movement_type=m.movement_type,
                quantity=abs(m.quantity_delta),
                unit_cost=m.unit_cost_at_movement or Decimal("0.0000"),
                total_cost=(abs(m.quantity_delta) * (m.unit_cost_at_movement or Decimal("0.0000"))).quantize(Decimal("0.0001")),
                balance_after=m.balance_after_movement,
                reference_type=m.reference_type,
                reference_id=m.reference_id,
                reason=m.reason,
                notes=m.notes,
                created_at=m.created_at,
                created_by_user_id=m.created_by_user_id,
            )
            for m in movements
        ]

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return PaginatedStockMovementsResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    # -------------------------------------------------------------------------
    # Reconciliation & Ledger Repair
    # -------------------------------------------------------------------------
    @staticmethod
    def reconcile_and_repair_projections(
        db: Session,
        business_id: uuid.UUID,
        store_id: uuid.UUID,
    ) -> ReconciliationReportResponse:
        """
        Audits and rebuilds stock balance projections directly from immutable stock movements.
        Repairs any corrupted or desynchronized current_quantity values.
        """
        ledger_sums = db.execute(
            select(
                StockMovement.variant_id,
                func.sum(StockMovement.base_quantity_delta).label("ledger_quantity"),
            )
            .where(
                and_(
                    StockMovement.business_id == business_id,
                    StockMovement.store_id == store_id,
                )
            )
            .group_by(StockMovement.variant_id)
        ).all()

        discrepancies: list[dict] = []

        for row in ledger_sums:
            v_id: uuid.UUID = row[0]
            ledger_qty = (row[1] or Decimal("0.0000")).quantize(Decimal("0.0001"))

            balance = db.execute(
                select(StockBalance)
                .where(
                    and_(
                        StockBalance.business_id == business_id,
                        StockBalance.store_id == store_id,
                        StockBalance.variant_id == v_id,
                    )
                )
                .with_for_update()
            ).scalar_one_or_none()

            current_qty = balance.current_quantity if balance else Decimal("0.0000")

            if current_qty != ledger_qty:
                discrepancy = {
                    "variant_id": str(v_id),
                    "recorded_balance": str(current_qty),
                    "ledger_calculated_balance": str(ledger_qty),
                    "variance": str(ledger_qty - current_qty),
                }
                discrepancies.append(discrepancy)

                if balance is None:
                    var = db.execute(select(ProductVariant).where(ProductVariant.id == v_id)).scalar_one_or_none()
                    balance = StockBalance(
                        id=uuid.uuid4(),
                        business_id=business_id,
                        store_id=store_id,
                        product_id=var.product_id if var else v_id,
                        variant_id=v_id,
                        current_quantity=ledger_qty,
                        moving_average_cost=var.cost_price or Decimal("0.0000") if var else Decimal("0.0000"),
                        min_stock_level=Decimal("0.0000"),
                        reorder_quantity=Decimal("0.0000"),
                        version=1,
                    )
                    db.add(balance)
                else:
                    balance.current_quantity = ledger_qty
                    balance.version += 1

        db.flush()

        return ReconciliationReportResponse(
            store_id=store_id,
            total_variants_checked=len(ledger_sums),
            variants_reconciled=len(ledger_sums),
            discrepancies_repaired=len(discrepancies),
            discrepancy_details=discrepancies,
            reconciled_at=datetime.now(timezone.utc),
        )
