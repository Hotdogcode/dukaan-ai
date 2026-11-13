"""Enhance inventory to variant level and stock movement ledger

Revision ID: 004_inventory_variant_ledger
Revises: 003_catalogue_enhancements
Create Date: 2026-11-13 10:00:00.000000

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "004_inventory_variant_ledger"
down_revision: Union[str, None] = "003_catalogue_enhancements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_TABLES = ["inventory_count_items"]


def upgrade() -> None:
    # ----------------------------------------------------
    # 1. Business Negative Stock Policy
    # ----------------------------------------------------
    op.add_column(
        "businesses",
        sa.Column("negative_stock_policy", sa.String(30), server_default="DISALLOW_NEGATIVE_STOCK", nullable=False),
    )

    # ----------------------------------------------------
    # 2. Stock Movements Enhancement (Variant-Level Tracking)
    # ----------------------------------------------------
    op.add_column(
        "stock_movements",
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True),
    )
    op.add_column(
        "stock_movements",
        sa.Column("uom_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True),
    )
    op.add_column(
        "stock_movements",
        sa.Column("base_quantity_delta", sa.Numeric(14, 4), nullable=True),
    )
    op.add_column(
        "stock_movements",
        sa.Column("reference_type", sa.String(50), server_default="MANUAL", nullable=False),
    )
    op.add_column(
        "stock_movements",
        sa.Column("reason", sa.String(255), nullable=True),
    )
    op.add_column(
        "stock_movements",
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "stock_movements",
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
    )
    op.add_column(
        "stock_movements",
        sa.Column("reversal_of_movement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stock_movements.id", ondelete="SET NULL"), nullable=True),
    )

    # Backfill variant_id and base_quantity_delta if any existing rows exist
    op.execute(sa.text("""
        UPDATE stock_movements sm
        SET variant_id = pv.id,
            base_quantity_delta = sm.quantity_delta
        FROM product_variants pv
        WHERE pv.product_id = sm.product_id
          AND sm.variant_id IS NULL;
    """))

    op.alter_column("stock_movements", "variant_id", nullable=False)
    op.create_index("ix_stock_movements_variant_query", "stock_movements", ["business_id", "store_id", "variant_id", "occurred_at"])

    # ----------------------------------------------------
    # 3. Stock Balances Enhancement (Variant-Level Projection)
    # ----------------------------------------------------
    op.add_column(
        "stock_balances",
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True),
    )
    op.add_column(
        "stock_balances",
        sa.Column("min_stock_level", sa.Numeric(14, 4), server_default="0.0000", nullable=False),
    )
    op.add_column(
        "stock_balances",
        sa.Column("reorder_quantity", sa.Numeric(14, 4), server_default="0.0000", nullable=False),
    )

    # Backfill variant_id on stock_balances
    op.execute(sa.text("""
        UPDATE stock_balances sb
        SET variant_id = pv.id
        FROM product_variants pv
        WHERE pv.product_id = sb.product_id
          AND sb.variant_id IS NULL;
    """))

    op.alter_column("stock_balances", "variant_id", nullable=False)
    
    # Drop old unique constraint on (business_id, store_id, product_id)
    try:
        op.drop_constraint("uq_stock_balance_business_store_product", "stock_balances", type_="unique")
    except Exception:
        pass

    op.create_unique_constraint(
        "uq_stock_balance_business_store_variant",
        "stock_balances",
        ["business_id", "store_id", "variant_id"],
    )
    op.create_index("ix_stock_balances_variant_lookup", "stock_balances", ["business_id", "store_id", "variant_id"])

    # ----------------------------------------------------
    # 4. Inventory Count Items Table
    # ----------------------------------------------------
    op.create_table(
        "inventory_count_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_count_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("expected_quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("counted_quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("variance_quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("session_id", "variant_id", name="uq_inventory_count_item_session_variant"),
    )

    # Enable RLS on inventory_count_items
    op.execute(sa.text("ALTER TABLE inventory_count_items ENABLE ROW LEVEL SECURITY;"))
    op.execute(sa.text("ALTER TABLE inventory_count_items FORCE ROW LEVEL SECURITY;"))
    op.execute(sa.text("""
        CREATE POLICY inventory_count_items_tenant_isolation_policy ON inventory_count_items
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
    # 5. Inventory Adjustments Enhancement
    # ----------------------------------------------------
    op.add_column(
        "inventory_adjustments",
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True),
    )
    op.add_column(
        "inventory_adjustments",
        sa.Column("movement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stock_movements.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "inventory_adjustments",
        sa.Column("adjustment_type", sa.String(30), server_default="MANUAL", nullable=False),
    )
    op.add_column(
        "inventory_adjustments",
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
    )

    op.execute(sa.text("""
        UPDATE inventory_adjustments ia
        SET variant_id = pv.id,
            created_by_user_id = ia.approved_by_user_id
        FROM product_variants pv
        WHERE pv.product_id = ia.product_id
          AND ia.variant_id IS NULL;
    """))

    op.alter_column("inventory_adjustments", "variant_id", nullable=False)
    op.alter_column("inventory_adjustments", "created_by_user_id", nullable=False)


def downgrade() -> None:
    op.drop_table("inventory_count_items")
    op.drop_column("inventory_adjustments", "created_by_user_id")
    op.drop_column("inventory_adjustments", "adjustment_type")
    op.drop_column("inventory_adjustments", "movement_id")
    op.drop_column("inventory_adjustments", "variant_id")

    op.drop_index("ix_stock_balances_variant_lookup", table_name="stock_balances")
    op.drop_constraint("uq_stock_balance_business_store_variant", "stock_balances", type_="unique")
    op.create_unique_constraint("uq_stock_balance_business_store_product", "stock_balances", ["business_id", "store_id", "product_id"])
    op.drop_column("stock_balances", "reorder_quantity")
    op.drop_column("stock_balances", "min_stock_level")
    op.drop_column("stock_balances", "variant_id")

    op.drop_index("ix_stock_movements_variant_query", table_name="stock_movements")
    op.drop_column("stock_movements", "reversal_of_movement_id")
    op.drop_column("stock_movements", "created_by_user_id")
    op.drop_column("stock_movements", "notes")
    op.drop_column("stock_movements", "reason")
    op.drop_column("stock_movements", "reference_type")
    op.drop_column("stock_movements", "base_quantity_delta")
    op.drop_column("stock_movements", "uom_id")
    op.drop_column("stock_movements", "variant_id")

    op.drop_column("businesses", "negative_stock_policy")
