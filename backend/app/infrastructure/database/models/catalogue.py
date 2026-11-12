import uuid
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin


class Brand(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Optional product brand definition per business."""
    __tablename__ = "brands"
    __table_args__ = (
        UniqueConstraint("business_id", "name", name="uq_brand_business_name"),
    )

    name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Categorical hierarchy for merchant products."""
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("business_id", "name", name="uq_category_business_name"),
    )

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    parent: Mapped["Category | None"] = relationship("Category", remote_side="Category.id", backref="subcategories")


class UnitOfMeasure(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Global and domain-standard units of measure (e.g. KG, GM, PCS, L, ML, DOZ)."""
    __tablename__ = "units_of_measure"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)  # MASS, VOLUME, COUNT
    is_fractional_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class StandardUnitConversion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Standard unit conversions (e.g. 1 KG = 1000 GM, 1 L = 1000 ML, 1 DOZ = 12 PCS)."""
    __tablename__ = "standard_unit_conversions"
    __table_args__ = (
        UniqueConstraint("from_uom_id", "to_uom_id", name="uq_std_unit_conversion"),
        CheckConstraint("multiplier > 0", name="chk_std_conversion_multiplier_positive"),
    )

    from_uom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="CASCADE"), nullable=False)
    to_uom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="CASCADE"), nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    dimension: Mapped[str] = mapped_column(String(20), nullable=False)  # MASS, VOLUME, COUNT

    from_uom: Mapped["UnitOfMeasure"] = relationship("UnitOfMeasure", foreign_keys=[from_uom_id])
    to_uom: Mapped["UnitOfMeasure"] = relationship("UnitOfMeasure", foreign_keys=[to_uom_id])


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Master product definition. Supports single products or multi-variant items."""
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("business_id", "sku", name="uq_product_business_sku"),
        CheckConstraint("selling_price <= mrp", name="chk_selling_price_le_mrp"),
        CheckConstraint("selling_price >= 0", name="chk_selling_price_non_negative"),
        CheckConstraint("mrp >= 0", name="chk_mrp_non_negative"),
        CheckConstraint("tax_rate_percent >= 0 AND tax_rate_percent <= 100", name="chk_tax_rate_percent_range"),
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    brand_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
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
    has_variants: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    # Relationships
    category: Mapped[Category | None] = relationship("Category")
    brand: Mapped[Brand | None] = relationship("Brand")
    base_uom: Mapped[UnitOfMeasure] = relationship("UnitOfMeasure", foreign_keys=[base_uom_id])
    barcodes: Mapped[list["ProductBarcode"]] = relationship("ProductBarcode", back_populates="product", cascade="all, delete-orphan")
    variants: Mapped[list["ProductVariant"]] = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    conversions: Mapped[list["UnitConversion"]] = relationship("UnitConversion", back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Specific sellable variant of a product (e.g. Parle-G 50g, 100g, 200g)."""
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("business_id", "sku", name="uq_variant_business_sku"),
        CheckConstraint("selling_price <= mrp", name="chk_variant_selling_price_le_mrp"),
        CheckConstraint("selling_price >= 0", name="chk_variant_selling_price_non_negative"),
        CheckConstraint("mrp >= 0", name="chk_variant_mrp_non_negative"),
        CheckConstraint("tax_rate_percent >= 0 AND tax_rate_percent <= 100", name="chk_variant_tax_rate_percent_range"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sku: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    base_uom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0.0000"), nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    mrp: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    is_tax_inclusive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="variants")
    base_uom: Mapped["UnitOfMeasure"] = relationship("UnitOfMeasure", foreign_keys=[base_uom_id])
    barcodes: Mapped[list["ProductBarcode"]] = relationship("ProductBarcode", back_populates="variant", cascade="all, delete-orphan")


class ProductBarcode(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    """Product barcode mapping enforcing tenant-scoped uniqueness."""
    __tablename__ = "product_barcodes"
    __table_args__ = (
        UniqueConstraint("business_id", "barcode", name="uq_product_barcode_business"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True)
    barcode: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    barcode_type: Mapped[str] = mapped_column(String(30), default="EAN_13", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="barcodes")
    variant: Mapped["ProductVariant | None"] = relationship("ProductVariant", back_populates="barcodes")


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
