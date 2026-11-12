import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin


class CashRegister(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Cash Drawer (Galla) active shift session and reconciliation."""
    __tablename__ = "cash_registers"

    opened_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    closed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    opening_float: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    expected_closing_cash: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    actual_closing_cash: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    variance: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)  # OPEN, CLOSED
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Expense(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Store operational petty expense."""
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_expense_amount_positive"),
    )

    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    cash_register_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cash_registers.id", ondelete="SET NULL"), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # RENT, ELECTRICITY, SALARY, MAINTENANCE, LOGISTICS, REFRESHMENTS, OTHER
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)  # CASH, UPI, BANK_TRANSFER
    recipient_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Payment(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Universal payment tender record across Sales, Khata Repayments, and Payouts."""
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_payment_amount_positive"),
    )

    payment_type: Mapped[str] = mapped_column(String(30), nullable=False)  # CUSTOMER_SALE, CUSTOMER_KHATA_REPAYMENT, SUPPLIER_PURCHASE_PAYOUT, EXPENSE_PAYOUT
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)  # CASH, UPI, BANK_TRANSFER, CUSTOMER_CREDIT
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="SETTLED", nullable=False)  # PENDING, SETTLED, FAILED, REFUNDED, REVERSED
    transaction_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cash_register_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cash_registers.id", ondelete="SET NULL"), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    allocations: Mapped[list["PaymentAllocation"]] = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")


class PaymentAllocation(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Links a payment to target operational entities."""
    __tablename__ = "payment_allocations"

    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)  # SALE, PURCHASE, CUSTOMER_ACCOUNT, EXPENSE
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    payment: Mapped["Payment"] = relationship("Payment", back_populates="allocations")


class CashMovement(Base, UUIDPrimaryKeyMixin, TenantMixin, StoreScopedMixin):
    """Detailed audit of cash ingress/egress within a Cash Register."""
    __tablename__ = "cash_movements"
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_cm_amount_positive"),
    )

    cash_register_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cash_registers.id", ondelete="CASCADE"), nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)  # FLOAT_IN, SALE_IN, KHATA_REPAYMENT_IN, EXPENSE_OUT, SUPPLIER_PAYOUT_OUT, FLOAT_OUT
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
