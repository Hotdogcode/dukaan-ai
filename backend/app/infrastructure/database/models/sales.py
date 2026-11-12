import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin


class Sale(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Counter POS Sale invoice header."""
    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("store_id", "invoice_number", name="uq_sale_store_invoice"),
        CheckConstraint("total_amount >= 0", name="chk_sale_total_non_negative"),
        CheckConstraint("paid_amount >= 0", name="chk_sale_paid_non_negative"),
        CheckConstraint("credit_amount >= 0", name="chk_sale_credit_non_negative"),
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    cashier_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)  # DRAFT, COMPLETED, PARTIALLY_PAID, RETURNED, VOIDED
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    client_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    items: Mapped[list["SaleItem"]] = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Line item in a counter sale preserving historical prices and costs."""
    __tablename__ = "sale_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_sale_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="chk_sale_item_price_non_negative"),
    )

    sale_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    uom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_cost_basis: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)  # COGS basis at sale time
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")


class SaleReturn(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Customer sale return record."""
    __tablename__ = "sale_returns"

    original_sale_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True)
    processed_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    return_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    refund_method: Mapped[str] = mapped_column(String(30), nullable=False)  # CASH, UPI, CUSTOMER_CREDIT
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    return_items: Mapped[list["SaleReturnItem"]] = relationship("SaleReturnItem", back_populates="sale_return", cascade="all, delete-orphan")


class SaleReturnItem(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Line items returned from a previous sale."""
    __tablename__ = "sale_return_items"
    __table_args__ = (
        CheckConstraint("quantity_returned > 0", name="chk_sale_return_qty_positive"),
    )

    sale_return_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sale_returns.id", ondelete="CASCADE"), nullable=False, index=True)
    original_sale_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sale_items.id", ondelete="RESTRICT"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity_returned: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    refund_unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    refund_line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_restockable: Mapped[bool] = mapped_column(default=True, nullable=False)

    sale_return: Mapped["SaleReturn"] = relationship("SaleReturn", back_populates="return_items")


class SaleReversal(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Audit record for same-day sale void / cancellation."""
    __tablename__ = "sale_reversals"

    sale_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="RESTRICT"), unique=True, nullable=False)
    authorized_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    reversal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
