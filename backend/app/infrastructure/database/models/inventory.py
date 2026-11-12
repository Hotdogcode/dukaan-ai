import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin


class StockMovement(Base, UUIDPrimaryKeyMixin, TenantMixin, StoreScopedMixin):
    """
    Authoritative, immutable stock movement journal.
    Stock balance is an algebraic sum of all historical movements.
    """
    __tablename__ = "stock_movements"
    __table_args__ = (
        Index("ix_stock_movements_query", "business_id", "store_id", "product_id", "occurred_at"),
        UniqueConstraint("business_id", "idempotency_key", name="uq_stock_movement_idempotency"),
        CheckConstraint("quantity_delta != 0", name="chk_stock_movement_qty_non_zero"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)  # PURCHASE_RECEIPT, SALE_DEDUCTION, SALE_RETURN, PURCHASE_RETURN, DAMAGE_SPOILAGE, AUDIT_ADJUSTMENT
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)  # Signed delta in BaseUnit
    unit_cost_at_movement: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    balance_after_movement: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    idempotency_key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StockBalance(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """
    Current stock projection cache per store and product.
    Optimistic concurrency protected via version counter.
    """
    __tablename__ = "stock_balances"
    __table_args__ = (
        UniqueConstraint("business_id", "store_id", "product_id", name="uq_stock_balance_business_store_product"),
        CheckConstraint("moving_average_cost >= 0", name="chk_stock_balance_cost_non_negative"),
        Index("ix_stock_balances_lookup", "business_id", "store_id", "product_id"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    current_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)
    moving_average_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)
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


class InventoryAdjustment(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Variance adjustment between physical count and system stock."""
    __tablename__ = "inventory_adjustments"

    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_count_sessions.id", ondelete="SET NULL"), nullable=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    system_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    counted_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    variance_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)  # counted - system
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    approved_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
