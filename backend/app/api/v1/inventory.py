"""
FastAPI Routes for Inventory Management, Stock Balances, Stock Movement Ledger,
Physical Stock Counting, and Projection Reconciliation.
Enforces business membership, granular role permissions, and tenant isolation.
"""

from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies.auth import (
    get_current_user,
    get_tenant_membership,
    require_permission,
)
from backend.app.application.inventory.service import InventoryService
from backend.app.core.security import Permissions
from backend.app.infrastructure.database.models import BusinessUser, User
from backend.app.infrastructure.database.session import get_db_session
from backend.app.schemas.inventory import (
    CompleteCountSessionResponse,
    InventoryCountItemCreate,
    InventoryCountItemResponse,
    InventoryCountSessionCreate,
    InventoryCountSessionResponse,
    InventorySummaryResponse,
    OpeningStockRequest,
    OpeningStockResponse,
    PaginatedStockMovementsResponse,
    ReconciliationReportResponse,
    StockAdjustmentRequest,
    StockAdjustmentResponse,
    StockDetailsResponse,
)

router = APIRouter(tags=["Inventory Management"])


# -----------------------------------------------------------------------------
# 1. Inventory Summary & Overview
# -----------------------------------------------------------------------------
@router.get(
    "/businesses/{business_id}/stores/{store_id}/inventory",
    response_model=InventorySummaryResponse,
    summary="Get Store Inventory Overview & Valuation",
    description="Returns paginated inventory summary, stock levels, and store valuation metrics.",
)
def get_inventory_summary(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.INVENTORY_READ))],
    db: Annotated[Session, Depends(get_db_session)],
    query: str | None = Query(default=None, description="Search query by name, SKU, or barcode"),
    category_id: uuid.UUID | None = Query(default=None, description="Filter by category ID"),
    low_stock_only: bool = Query(default=False, description="Filter only variants below minimum threshold"),
    out_of_stock_only: bool = Query(default=False, description="Filter only variants with zero or negative stock"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
) -> InventorySummaryResponse:
    return InventoryService.get_inventory_summary(
        db=db,
        business_id=business_id,
        store_id=store_id,
        query=query,
        category_id=category_id,
        low_stock_only=low_stock_only,
        out_of_stock_only=out_of_stock_only,
        page=page,
        limit=limit,
    )


# -----------------------------------------------------------------------------
# 2. Variant Stock Details
# -----------------------------------------------------------------------------
@router.get(
    "/businesses/{business_id}/stores/{store_id}/inventory/{variant_id}",
    response_model=StockDetailsResponse,
    summary="Get Variant Stock Details",
    description="Returns detailed stock balance, moving average cost, and status for a specific variant.",
)
def get_variant_stock_details(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    variant_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.INVENTORY_READ))],
    db: Annotated[Session, Depends(get_db_session)],
) -> StockDetailsResponse:
    return InventoryService.get_variant_stock_details(
        db=db,
        business_id=business_id,
        store_id=store_id,
        variant_id=variant_id,
    )


# -----------------------------------------------------------------------------
# 3. Stock Movement Ledger
# -----------------------------------------------------------------------------
@router.get(
    "/businesses/{business_id}/stores/{store_id}/inventory/{variant_id}/movements",
    response_model=PaginatedStockMovementsResponse,
    summary="Get Stock Movement Ledger",
    description="Returns paginated immutable movement history for a variant at a store.",
)
def get_stock_movements(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    variant_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.INVENTORY_READ))],
    db: Annotated[Session, Depends(get_db_session)],
    movement_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
) -> PaginatedStockMovementsResponse:
    return InventoryService.list_stock_movements(
        db=db,
        business_id=business_id,
        store_id=store_id,
        variant_id=variant_id,
        movement_type=movement_type,
        page=page,
        limit=limit,
    )


# -----------------------------------------------------------------------------
# 4. Opening Stock Entry
# -----------------------------------------------------------------------------
@router.post(
    "/businesses/{business_id}/stores/{store_id}/inventory/opening-stock",
    response_model=OpeningStockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Opening Stock",
    description="Records the initial opening stock balance for a product variant at a store.",
)
def record_opening_stock(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    payload: OpeningStockRequest,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.INVENTORY_OPENING_STOCK))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> OpeningStockResponse:
    return InventoryService.record_opening_stock(
        db=db,
        business_id=business_id,
        store_id=store_id,
        user_id=current_user.id,
        payload=payload,
    )


# -----------------------------------------------------------------------------
# 5. Stock Adjustments
# -----------------------------------------------------------------------------
@router.post(
    "/businesses/{business_id}/stores/{store_id}/inventory/adjustments",
    response_model=StockAdjustmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Stock Adjustment",
    description="Records manual additions, deductions, damage, or expiry adjustments with WAC updates.",
)
def record_stock_adjustment(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    payload: StockAdjustmentRequest,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.INVENTORY_ADJUST))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> StockAdjustmentResponse:
    return InventoryService.record_adjustment(
        db=db,
        business_id=business_id,
        store_id=store_id,
        user_id=current_user.id,
        payload=payload,
    )


# -----------------------------------------------------------------------------
# 6. Physical Stock Count Sessions
# -----------------------------------------------------------------------------
@router.post(
    "/businesses/{business_id}/stores/{store_id}/inventory/counts",
    response_model=InventoryCountSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Stock Count Session",
    description="Initiates a new physical inventory counting audit session.",
)
def create_count_session(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    payload: InventoryCountSessionCreate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.INVENTORY_COUNT))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> InventoryCountSessionResponse:
    return InventoryService.create_count_session(
        db=db,
        business_id=business_id,
        store_id=store_id,
        user_id=current_user.id,
        payload=payload,
    )


@router.get(
    "/businesses/{business_id}/stores/{store_id}/inventory/counts",
    response_model=list[InventoryCountSessionResponse],
    summary="List Stock Count Sessions",
    description="Lists all physical counting sessions for a store.",
)
def list_count_sessions(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.INVENTORY_READ))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[InventoryCountSessionResponse]:
    return InventoryService.list_count_sessions(
        db=db,
        business_id=business_id,
        store_id=store_id,
    )


@router.get(
    "/businesses/{business_id}/stores/{store_id}/inventory/counts/{count_id}",
    response_model=InventoryCountSessionResponse,
    summary="Get Stock Count Session Details",
    description="Retrieves a specific counting session along with recorded items and variances.",
)
def get_count_session(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    count_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.INVENTORY_READ))],
    db: Annotated[Session, Depends(get_db_session)],
) -> InventoryCountSessionResponse:
    return InventoryService.get_count_session(
        db=db,
        business_id=business_id,
        store_id=store_id,
        count_id=count_id,
    )


@router.post(
    "/businesses/{business_id}/stores/{store_id}/inventory/counts/{count_id}/items",
    response_model=InventoryCountItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Counted Item",
    description="Records or updates physical count for a variant in an open audit session.",
)
def add_count_item(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    count_id: uuid.UUID,
    payload: InventoryCountItemCreate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.INVENTORY_COUNT))],
    db: Annotated[Session, Depends(get_db_session)],
) -> InventoryCountItemResponse:
    return InventoryService.add_count_item(
        db=db,
        business_id=business_id,
        store_id=store_id,
        count_id=count_id,
        payload=payload,
    )


@router.post(
    "/businesses/{business_id}/stores/{store_id}/inventory/counts/{count_id}/complete",
    response_model=CompleteCountSessionResponse,
    summary="Complete Stock Count Session",
    description="Finalizes physical count audit, generates variance movements, and adjusts stock balances.",
)
def complete_count_session(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    count_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.INVENTORY_COUNT))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> CompleteCountSessionResponse:
    return InventoryService.complete_count_session(
        db=db,
        business_id=business_id,
        store_id=store_id,
        user_id=current_user.id,
        count_id=count_id,
    )


# -----------------------------------------------------------------------------
# 7. Inventory Reconciliation & Ledger Repair
# -----------------------------------------------------------------------------
@router.post(
    "/businesses/{business_id}/stores/{store_id}/inventory/reconciliation",
    response_model=ReconciliationReportResponse,
    summary="Reconcile and Repair Stock Projections",
    description="Audits store balances against immutable stock movements and repairs any detected discrepancies.",
)
def reconcile_inventory(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.INVENTORY_RECONCILE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ReconciliationReportResponse:
    return InventoryService.reconcile_and_repair_projections(
        db=db,
        business_id=business_id,
        store_id=store_id,
    )
