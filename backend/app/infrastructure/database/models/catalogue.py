import uuid
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Categorical hierarchy for merchant products."""
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("business_id", "name", name="uq_category_business_name"),
    )

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UnitOfMeasure(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Global and domain-standard units of measure (e.g. KG, GRAM, PIECE, LITRE)."""
    __tablename__ = "units_of_measure"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)  # MASS, VOLUME, COUNT
    is_fractional_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Master product SKU definition. Stock is tracked separately in inventory."""
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("business_id", "sku", name="uq_product_business_sku"),
        CheckConstraint("selling_price <= mrp", name="chk_selling_price_le_mrp"),
        CheckConstraint("selling_price >= 0", name="chk_selling_price_non_negative"),
        CheckConstraint("mrp >= 0", name="chk_mrp_non_negative"),
        CheckConstraint("tax_rate_percent >= 0 AND tax_rate_percent <= 100", name="chk_tax_rate_percent_range"),
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    hsn_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    base_uom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    mrp: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)
    tax_rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    is_tax_inclusive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reorder_threshold: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)
    is_loose_item: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    # Relationships
    barcodes: Mapped[list["ProductBarcode"]] = relationship("ProductBarcode", back_populates="product", cascade="all, delete-orphan")
    conversions: Mapped[list["UnitConversion"]] = relationship("UnitConversion", back_populates="product", cascade="all, delete-orphan")


class ProductBarcode(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Product barcode mapping enforcing tenant-scoped uniqueness."""
    __tablename__ = "product_barcodes"
    __table_args__ = (
        UniqueConstraint("business_id", "barcode", name="uq_product_barcode_business"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    barcode: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="barcodes")


class UnitConversion(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Defines product-specific unit conversions from transaction unit to base unit."""
    __tablename__ = "unit_conversions"
    __table_args__ = (
        UniqueConstraint("product_id", "from_uom_id", "to_uom_id", name="uq_unit_conversion_rule"),
        CheckConstraint("multiplier > 0", name="chk_conversion_multiplier_positive"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    from_uom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False)
    to_uom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="conversions")
