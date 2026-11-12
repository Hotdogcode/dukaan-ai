import uuid
from sqlalchemy import Boolean, CHAR, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Business(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """The root tenant entity owning stores, products, inventory, and accounts."""
    __tablename__ = "businesses"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(15), index=True, nullable=True)
    currency: Mapped[str] = mapped_column(CHAR(3), default="INR", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)
    primary_language: Mapped[str] = mapped_column(String(10), default="hi", nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def business_type(self) -> str | None:
        return self.settings.get("business_type") if isinstance(self.settings, dict) else None

    @property
    def owner_name(self) -> str | None:
        return self.settings.get("owner_name") if isinstance(self.settings, dict) else None

    # Relationships
    stores: Mapped[list["Store"]] = relationship("Store", back_populates="business", cascade="all, delete-orphan")
    members: Mapped[list["BusinessUser"]] = relationship("BusinessUser", back_populates="business", cascade="all, delete-orphan")


class BusinessUser(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Associates a User with a Business with an explicit Role and permissions."""
    __tablename__ = "business_users"
    __table_args__ = (
        UniqueConstraint("business_id", "user_id", name="uq_business_user"),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(30), default="CASHIER", nullable=False)  # OWNER, MANAGER, CASHIER
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="members")
    user: Mapped["backend.app.infrastructure.database.models.identity.User"] = relationship("backend.app.infrastructure.database.models.identity.User", back_populates="business_memberships")


class Store(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Physical branch/location owned by a Business."""
    __tablename__ = "stores"
    __table_args__ = (
        UniqueConstraint("business_id", "name", name="uq_store_business_name"),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(60), nullable=False)
    state: Mapped[str] = mapped_column(String(60), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(15), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="stores")
