import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin


class StockMovement(Base, UUIDPrimaryKeyMixin, TenantMixin, StoreScopedMixin):
    """
    Authoritative, immutable stock movement journal.
    Stock balance is an algebraic sum of all historical movements.
    """
    __tablename__ = "stock_movements"
    __table_args__ = (
        Index("ix_stock_movements_query", "business_id", "store_id", "product_id", "occurred_at"),
        Index("ix_stock_movements_variant_query", "business_id", "store_id", "variant_id", "occurred_at"),
        UniqueConstraint("business_id", "idempotency_key", name="uq_stock_movement_idempotency"),
        CheckConstraint("quantity_delta != 0", name="chk_stock_movement_qty_non_zero"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)  # OPENING_STOCK, PURCHASE_RECEIVED, SALE, SALE_RETURN, PURCHASE_RETURN, MANUAL_ADJUSTMENT_IN, MANUAL_ADJUSTMENT_OUT, DAMAGE, EXPIRY, TRANSFER_IN, TRANSFER_OUT, REVERSAL
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)  # Signed delta in BaseUnit
    uom_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    base_quantity_delta: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    unit_cost_at_movement: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    balance_after_movement: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(50), default="MANUAL", nullable=False)
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    reversal_of_movement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("stock_movements.id", ondelete="SET NULL"), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StockBalance(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """
    Current stock projection cache per store and variant.
    Optimistic concurrency protected via version counter.
    """
    __tablename__ = "stock_balances"
    __table_args__ = (
        UniqueConstraint("business_id", "store_id", "variant_id", name="uq_stock_balance_business_store_variant"),
        CheckConstraint("moving_average_cost >= 0", name="chk_stock_balance_cost_non_negative"),
        Index("ix_stock_balances_lookup", "business_id", "store_id", "product_id"),
        Index("ix_stock_balances_variant_lookup", "business_id", "store_id", "variant_id"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False, index=True)
    current_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)
    moving_average_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)
    min_stock_level: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)
    reorder_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)
    last_movement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("stock_movements.id", ondelete="SET NULL"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Optimistic concurrency lock


class InventoryCountSession(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Periodic physical inventory counting audit session."""
    __tablename__ = "inventory_count_sessions"

    conducted_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", nullable=False)  # OPEN, COMPLETED, CANCELLED
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["InventoryCountItem"]] = relationship("InventoryCountItem", back_populates="session", cascade="all, delete-orphan")


class InventoryCountItem(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Line item within a physical inventory count session."""
    __tablename__ = "inventory_count_items"
    __table_args__ = (
        UniqueConstraint("session_id", "variant_id", name="uq_inventory_count_item_session_variant"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_count_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False, index=True)
    expected_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    counted_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    variance_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)  # counted - expected
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    session: Mapped["InventoryCountSession"] = relationship("InventoryCountSession", back_populates="items")


class InventoryAdjustment(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Variance adjustment between physical count and system stock or manual correction."""
    __tablename__ = "inventory_adjustments"

    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_count_sessions.id", ondelete="SET NULL"), nullable=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False, index=True)
    movement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("stock_movements.id", ondelete="SET NULL"), nullable=True)
    adjustment_type: Mapped[str] = mapped_column(String(30), default="MANUAL", nullable=False)  # MANUAL_IN, MANUAL_OUT, DAMAGE, EXPIRY, COUNT_CORRECTION
    system_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    counted_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    variance_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    approved_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
