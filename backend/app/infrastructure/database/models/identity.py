import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Platform user who can own or belong to multiple businesses."""
    __tablename__ = "users"

    phone_number: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship("RefreshSession", back_populates="user", cascade="all, delete-orphan")
    business_memberships: Mapped[list["BusinessUser"]] = relationship("BusinessUser", back_populates="user", cascade="all, delete-orphan")


class RefreshSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User authentication session tokens."""
    __tablename__ = "refresh_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("device_registrations.id", ondelete="SET NULL"), nullable=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_sessions")
