import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin


class SupplierLedgerEntry(Base, UUIDPrimaryKeyMixin, TenantMixin, StoreScopedMixin):
    """Immutable ledger of wholesale liabilities, payments, and debit notes."""
    __tablename__ = "supplier_ledger_entries"
    __table_args__ = (
        Index("ix_supplier_ledger_timeline", "business_id", "supplier_id", "occurred_at"),
        CheckConstraint("amount > 0", name="chk_sle_amount_positive"),
    )

    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_type: Mapped[str] = mapped_column(String(30), nullable=False)  # PURCHASE_LIABILITY_CREDIT, SETTLEMENT_PAYMENT_DEBIT, DEBIT_NOTE_ADJUSTMENT
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    running_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)  # PurchaseId, PaymentId, or ReturnId
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SupplierPaymentAllocation(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Allocates a payment payout against specific wholesale purchase bills."""
    __tablename__ = "supplier_payment_allocations"

    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    purchase_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchases.id", ondelete="RESTRICT"), nullable=False, index=True)
    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
