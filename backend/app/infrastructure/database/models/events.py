import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin


class BusinessEvent(Base, UUIDPrimaryKeyMixin, TenantMixin):
    """
    Transactional Outbox event store.
    Captures domain events inside the same database transaction as aggregate state mutations.
    """
    __tablename__ = "business_events"
    __table_args__ = (
        Index("ix_business_events_type_time", "business_id", "event_type", "occurred_at"),
    )

    store_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="SET NULL"), nullable=True, index=True)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(60), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    event_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditLog(Base, UUIDPrimaryKeyMixin, TenantMixin):
    """Immutable administrative and security audit trail."""
    __tablename__ = "audit_logs"

    store_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_table: Mapped[str] = mapped_column(String(60), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    changes_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IdempotencyKey(Base, UUIDPrimaryKeyMixin, TenantMixin):
    """
    Ensures safe, deduplicated client-to-server transaction ingestion.
    Prevents duplicate financial and stock entries during offline retries.
    """
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("business_id", "idempotency_key", name="uq_tenant_idempotency_key"),
    )

    idempotency_key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PROCESSING", nullable=False)  # PROCESSING, COMPLETED, FAILED
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
