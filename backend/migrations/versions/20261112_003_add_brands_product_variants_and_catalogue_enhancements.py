"""Add brands, product variants, and catalogue enhancements

Revision ID: 003_catalogue_enhancements
Revises: 002_store_primary_and_timezone
Create Date: 2026-11-12 18:00:00.000000

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "003_catalogue_enhancements"
down_revision: Union[str, None] = "002_store_primary_and_timezone"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_TABLES = ["brands", "product_variants"]


def upgrade() -> None:
    # ----------------------------------------------------
    # 1. Brands Table
    # ----------------------------------------------------
    op.create_table(
        "brands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(80), nullable=False, index=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "name", name="uq_brand_business_name"),
    )

    # Enable RLS on brands
    op.execute(sa.text("ALTER TABLE brands ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("ALTER TABLE brands FORCE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY brands_tenant_isolation_policy ON brands
        FOR ALL
        USING (
            NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL
            OR business_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
        WITH CHECK (
            NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL
            OR business_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        );
    """))

    # ----------------------------------------------------
    # 2. Categories Enhancement (is_system flag)
    # ----------------------------------------------------
    op.add_column(
        "categories",
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    # ----------------------------------------------------
    # 3. Products Enhancement (brand_id, description, image_url, has_variants)
    # ----------------------------------------------------
    op.add_column(
        "products",
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    op.add_column(
        "products",
        sa.Column("description", sa.String(1000), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("image_url", sa.String(500), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("has_variants", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    # ----------------------------------------------------
    # 4. Product Variants Table
    # ----------------------------------------------------
    op.create_table(
        "product_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("variant_name", sa.String(100), nullable=False),
        sa.Column("sku", sa.String(60), nullable=False, index=True),
        sa.Column("base_uom_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cost_price", sa.Numeric(14, 4), server_default=sa.text("0.0000"), nullable=False),
        sa.Column("selling_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("mrp", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax_rate_percent", sa.Numeric(5, 2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("is_tax_inclusive", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "sku", name="uq_variant_business_sku"),
        sa.CheckConstraint("selling_price <= mrp", name="chk_variant_selling_price_le_mrp"),
        sa.CheckConstraint("selling_price >= 0", name="chk_variant_selling_price_non_negative"),
        sa.CheckConstraint("mrp >= 0", name="chk_variant_mrp_non_negative"),
        sa.CheckConstraint("tax_rate_percent >= 0 AND tax_rate_percent <= 100", name="chk_variant_tax_rate_percent_range"),
    )

    # Enable RLS on product_variants
    op.execute(sa.text("ALTER TABLE product_variants ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("ALTER TABLE product_variants FORCE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY product_variants_tenant_isolation_policy ON product_variants
        FOR ALL
        USING (
            NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL
            OR business_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
        WITH CHECK (
            NULLIF(current_setting('app.current_tenant_id', true), '') IS NULL
            OR business_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        );
    """))

    # ----------------------------------------------------
    # 5. Product Barcodes Enhancement (variant_id, barcode_type)
    # ----------------------------------------------------
    op.add_column(
        "product_barcodes",
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True),
    )
    op.add_column(
        "product_barcodes",
        sa.Column("barcode_type", sa.String(30), server_default="EAN_13", nullable=False),
    )

    # ----------------------------------------------------
    # 6. Standard Unit Conversions Table
    # ----------------------------------------------------
    op.create_table(
        "standard_unit_conversions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("from_uom_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units_of_measure.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_uom_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units_of_measure.id", ondelete="CASCADE"), nullable=False),
        sa.Column("multiplier", sa.Numeric(14, 6), nullable=False),
        sa.Column("dimension", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("from_uom_id", "to_uom_id", name="uq_std_unit_conversion"),
        sa.CheckConstraint("multiplier > 0", name="chk_std_conversion_multiplier_positive"),
    )

    # ----------------------------------------------------
    # 7. Seed Standard Units of Measure & Conversions
    # ----------------------------------------------------
    uom_table = sa.table(
        "units_of_measure",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("category", sa.String),
        sa.column("is_fractional_allowed", sa.Boolean),
    )

    # Fixed UUIDs for deterministic reference data
    kg_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    gm_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    l_id = uuid.UUID("00000000-0000-0000-0000-000000000003")
    ml_id = uuid.UUID("00000000-0000-0000-0000-000000000004")
    pcs_id = uuid.UUID("00000000-0000-0000-0000-000000000005")
    pkt_id = uuid.UUID("00000000-0000-0000-0000-000000000006")
    box_id = uuid.UUID("00000000-0000-0000-0000-000000000007")
    btl_id = uuid.UUID("00000000-0000-0000-0000-000000000008")
    doz_id = uuid.UUID("00000000-0000-0000-0000-000000000009")

    op.execute(sa.text("""
        INSERT INTO units_of_measure (id, code, name, category, is_fractional_allowed, created_at, updated_at)
        VALUES
            ('00000000-0000-0000-0000-000000000001', 'KG', 'Kilogram', 'MASS', true, now(), now()),
            ('00000000-0000-0000-0000-000000000002', 'GM', 'Gram', 'MASS', true, now(), now()),
            ('00000000-0000-0000-0000-000000000003', 'L', 'Litre', 'VOLUME', true, now(), now()),
            ('00000000-0000-0000-0000-000000000004', 'ML', 'Millilitre', 'VOLUME', true, now(), now()),
            ('00000000-0000-0000-0000-000000000005', 'PCS', 'Piece', 'COUNT', false, now(), now()),
            ('00000000-0000-0000-0000-000000000006', 'PKT', 'Packet', 'COUNT', false, now(), now()),
            ('00000000-0000-0000-0000-000000000007', 'BOX', 'Box', 'COUNT', false, now(), now()),
            ('00000000-0000-0000-0000-000000000008', 'BTL', 'Bottle', 'COUNT', false, now(), now()),
            ('00000000-0000-0000-0000-000000000009', 'DOZ', 'Dozen', 'COUNT', true, now(), now())
        ON CONFLICT (code) DO NOTHING;
    """))

    # Seed standard conversions
    op.execute(sa.text("""
        INSERT INTO standard_unit_conversions (id, from_uom_id, to_uom_id, multiplier, dimension, created_at, updated_at)
        VALUES
            ('00000000-0000-0000-0001-000000000001', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 1000.0, 'MASS', now(), now()),
            ('00000000-0000-0000-0001-000000000002', '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 0.001, 'MASS', now(), now()),
            ('00000000-0000-0000-0001-000000000003', '00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000004', 1000.0, 'VOLUME', now(), now()),
            ('00000000-0000-0000-0001-000000000004', '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000003', 0.001, 'VOLUME', now(), now()),
            ('00000000-0000-0000-0001-000000000005', '00000000-0000-0000-0000-000000000009', '00000000-0000-0000-0000-000000000005', 12.0, 'COUNT', now(), now()),
            ('00000000-0000-0000-0001-000000000006', '00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000009', 0.083333, 'COUNT', now(), now())
        ON CONFLICT DO NOTHING;
    """))


def downgrade() -> None:
    op.drop_table("standard_unit_conversions")
    op.drop_column("product_barcodes", "barcode_type")
    op.drop_column("product_barcodes", "variant_id")
    op.execute(sa.text("DROP POLICY IF EXISTS product_variants_tenant_isolation_policy ON product_variants;"))
    op.drop_table("product_variants")
    op.drop_column("products", "has_variants")
    op.drop_column("products", "image_url")
    op.drop_column("products", "description")
    op.drop_column("products", "brand_id")
    op.drop_column("categories", "is_system")
    op.execute(sa.text("DROP POLICY IF EXISTS brands_tenant_isolation_policy ON brands;"))
    op.drop_table("brands")
