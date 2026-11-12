import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin


class Customer(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Customer profile and Bahi-Khata ledger balance."""
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("business_id", "phone_number", name="uq_customer_business_phone"),
    )

    full_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)  # Positive = owes store; Negative = advance
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    ledger_entries: Mapped[list["CustomerLedgerEntry"]] = relationship("CustomerLedgerEntry", back_populates="customer", cascade="all, delete-orphan")


class CustomerLedgerEntry(Base, UUIDPrimaryKeyMixin, TenantMixin, StoreScopedMixin):
    """
    Immutable Customer Khata credit/debit transaction log.
    Repayments strictly reduce outstanding balance without creating sales revenue.
    """
    __tablename__ = "customer_ledger_entries"
    __table_args__ = (
        Index("ix_customer_ledger_timeline", "business_id", "customer_id", "occurred_at"),
        CheckConstraint("amount > 0", name="chk_cle_amount_positive"),
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_type: Mapped[str] = mapped_column(String(30), nullable=False)  # CREDIT_SALE_DEBIT, PAYMENT_CREDIT, ADJUSTMENT_DEBIT, ADJUSTMENT_CREDIT, ADVANCE_DEPOSIT
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    running_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)  # SaleId or PaymentId
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="ledger_entries")


class CustomerPaymentAllocation(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Associates a customer repayment with specific prior credit sales."""
    __tablename__ = "customer_payment_allocations"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
