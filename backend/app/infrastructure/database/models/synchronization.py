import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin


class DeviceRegistration(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Registered Android terminal device authorized for offline operations."""
    __tablename__ = "device_registrations"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    fcm_token: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Firebase Cloud Messaging push token
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SyncDevice(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin):
    """Store counter device tracking hardware fingerprint and sync state."""
    __tablename__ = "sync_devices"
    __table_args__ = (
        UniqueConstraint("business_id", "device_fingerprint", name="uq_device_fingerprint"),
    )

    device_fingerprint: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    app_version: Mapped[str] = mapped_column(String(30), nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SyncOperation(Base, UUIDPrimaryKeyMixin, TenantMixin):
    """
    Log of client-generated offline mutations pushed to the server.
    Ensures idempotent processing and audit of conflict resolutions.
    """
    __tablename__ = "sync_operations"
    __table_args__ = (
        UniqueConstraint("device_id", "operation_id", name="uq_device_operation"),
    )

    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sync_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    operation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)  # Client-generated UUID
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # SALE_PUSH, STOCK_MOVEMENT_PUSH, KHATA_PAYMENT_PUSH, EXPENSE_PUSH
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="QUEUED", nullable=False)  # QUEUED, PROCESSED, REJECTED, CONFLICT_RESOLVED
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    server_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
