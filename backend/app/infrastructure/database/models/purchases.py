import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin


class Supplier(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Distributor or wholesale vendor profile."""
    __tablename__ = "suppliers"
    __table_args__ = (
        UniqueConstraint("business_id", "phone_number", name="uq_supplier_business_phone"),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(15), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_payable_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class Purchase(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Inward distributor procurement bill."""
    __tablename__ = "purchases"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_purchase_total_non_negative"),
        CheckConstraint("paid_amount >= 0", name="chk_purchase_paid_non_negative"),
        CheckConstraint("liability_amount >= 0", name="chk_purchase_liability_non_negative"),
    )

    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    received_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    supplier_invoice_number: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="RECEIVED", nullable=False)  # DRAFT, RECEIVED, PARTIALLY_PAID, SETTLED, RETURNED
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    liability_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    purchase_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    items: Mapped[list["PurchaseItem"]] = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")


class PurchaseItem(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Line item in a wholesale purchase bill."""
    __tablename__ = "purchase_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_purchase_item_qty_positive"),
        CheckConstraint("unit_cost >= 0", name="chk_purchase_item_cost_non_negative"),
    )

    purchase_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    uom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="items")


class PurchaseReturn(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Return of damaged or rejected goods to a supplier."""
    __tablename__ = "purchase_returns"

    purchase_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchases.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    debit_note_number: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    total_debit_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)

    return_items: Mapped[list["PurchaseReturnItem"]] = relationship("PurchaseReturnItem", back_populates="purchase_return", cascade="all, delete-orphan")


class PurchaseReturnItem(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Line item in a supplier purchase return."""
    __tablename__ = "purchase_return_items"
    __table_args__ = (
        CheckConstraint("quantity_returned > 0", name="chk_purchase_return_qty_positive"),
    )

    purchase_return_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_returns.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity_returned: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    debit_line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    purchase_return: Mapped["PurchaseReturn"] = relationship("PurchaseReturn", back_populates="return_items")
