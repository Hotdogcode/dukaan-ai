"""Initial production database schema with RLS and constraints

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-12 11:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# List of all tenant-owned tables requiring PostgreSQL Row-Level Security (RLS)
TENANT_TABLES = [
    "stores",
    "business_users",
    "categories",
    "products",
    "product_barcodes",
    "unit_conversions",
    "sales",
    "sale_items",
    "sale_returns",
    "sale_return_items",
    "sale_reversals",
    "suppliers",
    "purchases",
    "purchase_items",
    "purchase_returns",
    "purchase_return_items",
    "stock_movements",
    "stock_balances",
    "inventory_count_sessions",
    "inventory_adjustments",
    "customers",
    "customer_ledger_entries",
    "customer_payment_allocations",
    "supplier_ledger_entries",
    "supplier_payment_allocations",
    "cash_registers",
    "expenses",
    "payments",
    "payment_allocations",
    "cash_movements",
    "business_events",
    "audit_logs",
    "idempotency_keys",
    "device_registrations",
    "sync_devices",
    "sync_operations",
    "ai_conversations",
    "ai_messages",
    "ai_actions",
]


def upgrade() -> None:
    # ----------------------------------------------------
    # 1. Identity & Tenancy
    # ----------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("phone_number", sa.String(15), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_superadmin", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "businesses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("legal_name", sa.String(200), nullable=True),
        sa.Column("gstin", sa.String(15), nullable=True),
        sa.Column("currency", sa.CHAR(3), server_default="INR", nullable=False),
        sa.Column("timezone", sa.String(50), server_default="Asia/Kolkata", nullable=False),
        sa.Column("primary_language", sa.String(10), server_default="hi", nullable=False),
        sa.Column("settings", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_businesses_gstin", "businesses", ["gstin"])

    op.create_table(
        "business_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(30), server_default="CASHIER", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "user_id", name="uq_business_user"),
    )
    op.create_index("ix_business_users_business_id", "business_users", ["business_id"])
    op.create_index("ix_business_users_user_id", "business_users", ["user_id"])

    op.create_table(
        "stores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("code", sa.String(30), nullable=True),
        sa.Column("address_line1", sa.String(255), nullable=False),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(60), nullable=False),
        sa.Column("state", sa.String(60), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=False),
        sa.Column("phone_number", sa.String(15), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "name", name="uq_store_business_name"),
    )
    op.create_index("ix_stores_business_id", "stores", ["business_id"])

    # ----------------------------------------------------
    # 2. Product Catalogue
    # ----------------------------------------------------
    op.create_table(
        "units_of_measure",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("is_fractional_allowed", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_units_of_measure_code", "units_of_measure", ["code"], unique=True)

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "name", name="uq_category_business_name"),
    )
    op.create_index("ix_categories_business_id", "categories", ["business_id"])

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sku", sa.String(60), nullable=False),
        sa.Column("hsn_code", sa.String(20), nullable=True),
        sa.Column("base_uom_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("selling_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("mrp", sa.Numeric(14, 2), nullable=False),
        sa.Column("cost_price", sa.Numeric(14, 4), server_default="0.0000", nullable=False),
        sa.Column("tax_rate_percent", sa.Numeric(5, 2), server_default="0.00", nullable=False),
        sa.Column("is_tax_inclusive", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("reorder_threshold", sa.Numeric(14, 4), server_default="0.0000", nullable=False),
        sa.Column("is_loose_item", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "sku", name="uq_product_business_sku"),
        sa.CheckConstraint("selling_price <= mrp", name="chk_selling_price_le_mrp"),
        sa.CheckConstraint("selling_price >= 0", name="chk_selling_price_non_negative"),
        sa.CheckConstraint("mrp >= 0", name="chk_mrp_non_negative"),
        sa.CheckConstraint("tax_rate_percent >= 0 AND tax_rate_percent <= 100", name="chk_tax_rate_percent_range"),
    )
    op.create_index("ix_products_business_id", "products", ["business_id"])
    op.create_index("ix_products_sku", "products", ["sku"])
    op.create_index("ix_products_name", "products", ["name"])

    op.create_table(
        "product_barcodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("barcode", sa.String(60), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "barcode", name="uq_product_barcode_business"),
    )
    op.create_index("ix_product_barcodes_business_barcode", "product_barcodes", ["business_id", "barcode"])

    op.create_table(
        "unit_conversions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_uom_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("to_uom_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("multiplier", sa.Numeric(14, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("product_id", "from_uom_id", "to_uom_id", name="uq_unit_conversion_rule"),
        sa.CheckConstraint("multiplier > 0", name="chk_conversion_multiplier_positive"),
    )

    # ----------------------------------------------------
    # 3. Customer Khata
    # ----------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("phone_number", sa.String(15), nullable=False),
        sa.Column("credit_limit", sa.Numeric(14, 2), nullable=True),
        sa.Column("current_balance", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "phone_number", name="uq_customer_business_phone"),
    )
    op.create_index("ix_customers_business_phone", "customers", ["business_id", "phone_number"])
    op.create_index("ix_customers_business_name", "customers", ["business_id", "full_name"])

    # ----------------------------------------------------
    # 4. Sales & Invoicing
    # ----------------------------------------------------
    op.create_table(
        "sales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cashier_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("invoice_number", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), server_default="COMPLETED", nullable=False),
        sa.Column("subtotal_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("tax_amount", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("credit_amount", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("client_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("store_id", "invoice_number", name="uq_sale_store_invoice"),
        sa.CheckConstraint("total_amount >= 0", name="chk_sale_total_non_negative"),
        sa.CheckConstraint("paid_amount >= 0", name="chk_sale_paid_non_negative"),
        sa.CheckConstraint("credit_amount >= 0", name="chk_sale_credit_non_negative"),
    )
    op.create_index("ix_sales_business_store_occurred", "sales", ["business_id", "store_id", "occurred_at"])
    op.create_index("ix_sales_customer", "sales", ["business_id", "customer_id"])

    op.create_table(
        "sale_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sale_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("uom_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("unit_cost_basis", sa.Numeric(14, 4), server_default="0.0000", nullable=False),
        sa.Column("discount_amount", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("tax_amount", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="chk_sale_item_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="chk_sale_item_price_non_negative"),
    )
    op.create_index("ix_sale_items_sale_id", "sale_items", ["sale_id"])
    op.create_index("ix_sale_items_product_id", "sale_items", ["product_id"])

    op.create_table(
        "sale_returns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("original_sale_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("processed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("return_number", sa.String(50), unique=True, nullable=False),
        sa.Column("refund_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("refund_method", sa.String(30), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "sale_return_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sale_return_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sale_returns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_sale_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sale_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity_returned", sa.Numeric(14, 4), nullable=False),
        sa.Column("refund_unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("refund_line_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("is_restockable", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity_returned > 0", name="chk_sale_return_qty_positive"),
    )

    op.create_table(
        "sale_reversals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sale_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sales.id", ondelete="RESTRICT"), unique=True, nullable=False),
        sa.Column("authorized_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("reversal_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ----------------------------------------------------
    # 5. Suppliers & Purchasing
    # ----------------------------------------------------
    op.create_table(
        "suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("contact_person", sa.String(120), nullable=True),
        sa.Column("phone_number", sa.String(15), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("gstin", sa.String(15), nullable=True),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("payment_terms_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("current_payable_balance", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "phone_number", name="uq_supplier_business_phone"),
    )
    op.create_index("ix_suppliers_business_name", "suppliers", ["business_id", "name"])

    op.create_table(
        "purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("received_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("supplier_invoice_number", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), server_default="RECEIVED", nullable=False),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("paid_amount", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("liability_amount", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("purchase_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("total_amount >= 0", name="chk_purchase_total_non_negative"),
        sa.CheckConstraint("paid_amount >= 0", name="chk_purchase_paid_non_negative"),
        sa.CheckConstraint("liability_amount >= 0", name="chk_purchase_liability_non_negative"),
    )
    op.create_index("ix_purchases_business_store_date", "purchases", ["business_id", "store_id", "purchase_date"])
    op.create_index("ix_purchases_supplier", "purchases", ["business_id", "supplier_id"])

    op.create_table(
        "purchase_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("uom_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(14, 4), nullable=False),
        sa.Column("tax_amount", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("line_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="chk_purchase_item_qty_positive"),
        sa.CheckConstraint("unit_cost >= 0", name="chk_purchase_item_cost_non_negative"),
    )

    op.create_table(
        "purchase_returns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("purchases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("debit_note_number", sa.String(80), unique=True, nullable=False),
        sa.Column("total_debit_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "purchase_return_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_return_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("purchase_returns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity_returned", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(14, 4), nullable=False),
        sa.Column("debit_line_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity_returned > 0", name="chk_purchase_return_qty_positive"),
    )

    # ----------------------------------------------------
    # 6. Inventory & Stock Ledger
    # ----------------------------------------------------
    op.create_table(
        "stock_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("movement_type", sa.String(30), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_cost_at_movement", sa.Numeric(14, 4), nullable=True),
        sa.Column("balance_after_movement", sa.Numeric(14, 4), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("business_id", "idempotency_key", name="uq_stock_movement_idempotency"),
        sa.CheckConstraint("quantity_delta != 0", name="chk_stock_movement_qty_non_zero"),
    )
    op.create_index("ix_stock_movements_query", "stock_movements", ["business_id", "store_id", "product_id", "occurred_at"])

    op.create_table(
        "stock_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("current_quantity", sa.Numeric(14, 4), server_default="0.0000", nullable=False),
        sa.Column("moving_average_cost", sa.Numeric(14, 4), server_default="0.0000", nullable=False),
        sa.Column("last_movement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stock_movements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "store_id", "product_id", name="uq_stock_balance_business_store_product"),
        sa.CheckConstraint("moving_average_cost >= 0", name="chk_stock_balance_cost_non_negative"),
    )
    op.create_index("ix_stock_balances_lookup", "stock_balances", ["business_id", "store_id", "product_id"])

    op.create_table(
        "inventory_count_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("conducted_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(30), server_default="OPEN", nullable=False),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "inventory_adjustments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_count_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("system_quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("counted_quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("variance_quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ----------------------------------------------------
    # 7. Customer & Supplier Ledgers
    # ----------------------------------------------------
    op.create_table(
        "customer_ledger_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entry_type", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("running_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="chk_cle_amount_positive"),
    )
    op.create_index("ix_customer_ledger_timeline", "customer_ledger_entries", ["business_id", "customer_id", "occurred_at"])

    op.create_table(
        "supplier_ledger_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entry_type", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("running_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="chk_sle_amount_positive"),
    )
    op.create_index("ix_supplier_ledger_timeline", "supplier_ledger_entries", ["business_id", "supplier_id", "occurred_at"])

    # ----------------------------------------------------
    # 8. Financial Management (Cash Register, Expenses, Payments)
    # ----------------------------------------------------
    op.create_table(
        "cash_registers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("opened_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("closed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("opening_float", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("expected_closing_cash", sa.Numeric(14, 2), nullable=True),
        sa.Column("actual_closing_cash", sa.Numeric(14, 2), nullable=True),
        sa.Column("variance", sa.Numeric(14, 2), nullable=True),
        sa.Column("status", sa.String(20), server_default="OPEN", nullable=False),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "expenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cash_register_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cash_registers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("payment_method", sa.String(30), nullable=False),
        sa.Column("recipient_name", sa.String(150), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="chk_expense_amount_positive"),
    )

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("payment_type", sa.String(30), nullable=False),
        sa.Column("payment_method", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(30), server_default="SETTLED", nullable=False),
        sa.Column("transaction_reference", sa.String(120), nullable=True),
        sa.Column("cash_register_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cash_registers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="chk_payment_amount_positive"),
    )
    op.create_index("ix_payments_store_occurred", "payments", ["business_id", "store_id", "occurred_at"])

    op.create_table(
        "payment_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", sa.String(30), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "customer_payment_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sale_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sales.id", ondelete="SET NULL"), nullable=True),
        sa.Column("allocated_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "supplier_payment_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("purchases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "cash_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cash_register_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cash_registers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movement_type", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="chk_cm_amount_positive"),
    )

    # ----------------------------------------------------
    # 9. Events, Audits & Idempotency
    # ----------------------------------------------------
    op.create_table(
        "business_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="SET NULL"), nullable=True),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_type", sa.String(60), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_payload", postgresql.JSONB(), nullable=False),
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_business_events_type_time", "business_events", ["business_id", "event_type", "occurred_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target_table", sa.String(60), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("changes_json", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "idempotency_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="PROCESSING", nullable=False),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("business_id", "idempotency_key", name="uq_tenant_idempotency_key"),
    )
    op.create_index("ix_idempotency_keys_lookup", "idempotency_keys", ["business_id", "idempotency_key"])

    # ----------------------------------------------------
    # 10. Devices & Synchronization
    # ----------------------------------------------------
    op.create_table(
        "device_registrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_name", sa.String(100), nullable=False),
        sa.Column("fcm_token", sa.String(255), nullable=True),
        sa.Column("is_trusted", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "refresh_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("device_registrations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "sync_devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("device_fingerprint", sa.String(150), nullable=False),
        sa.Column("device_name", sa.String(100), nullable=False),
        sa.Column("app_version", sa.String(30), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "device_fingerprint", name="uq_device_fingerprint"),
    )

    op.create_table(
        "sync_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sync_devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_type", sa.String(50), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(30), server_default="QUEUED", nullable=False),
        sa.Column("error_message", sa.String(255), nullable=True),
        sa.Column("client_occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("server_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("device_id", "operation_id", name="uq_device_operation"),
    )

    # ----------------------------------------------------
    # 11. AI Assistant & Conversations
    # ----------------------------------------------------
    op.create_table(
        "ai_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("session_title", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "ai_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_type", sa.String(20), nullable=False),
        sa.Column("raw_utterance", sa.Text(), nullable=False),
        sa.Column("intent_detected", sa.String(60), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("structured_payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "ai_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("proposed_payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(30), server_default="PROPOSED", nullable=False),
        sa.Column("executed_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confirmed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ----------------------------------------------------
    # 12. PostgreSQL Row-Level Security (RLS) Policies
    # ----------------------------------------------------
    # Enable RLS on all tenant-owned tables and configure restrictive tenant isolation
    for table in TENANT_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
        op.execute(sa.text(
            f"""
            CREATE POLICY {table}_tenant_isolation_policy ON {table}
            AS RESTRICTIVE
            USING (
                current_setting('app.bypass_rls', true) = 'on'
                OR business_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            )
            WITH CHECK (
                current_setting('app.bypass_rls', true) = 'on'
                OR business_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            );
            """
        ))


def downgrade() -> None:
    # Disable RLS and drop tables in reverse dependency order
    for table in reversed(TENANT_TABLES):
        op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};"))
        op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;"))

    tables_in_order = [
        "ai_actions",
        "ai_messages",
        "ai_conversations",
        "sync_operations",
        "sync_devices",
        "refresh_sessions",
        "device_registrations",
        "idempotency_keys",
        "audit_logs",
        "business_events",
        "cash_movements",
        "supplier_payment_allocations",
        "customer_payment_allocations",
        "payment_allocations",
        "payments",
        "expenses",
        "cash_registers",
        "supplier_ledger_entries",
        "customer_ledger_entries",
        "inventory_adjustments",
        "inventory_count_sessions",
        "stock_balances",
        "stock_movements",
        "purchase_return_items",
        "purchase_returns",
        "purchase_items",
        "purchases",
        "suppliers",
        "sale_reversals",
        "sale_return_items",
        "sale_returns",
        "sale_items",
        "sales",
        "customers",
        "unit_conversions",
        "product_barcodes",
        "products",
        "categories",
        "units_of_measure",
        "stores",
        "business_users",
        "businesses",
        "users",
    ]

    for table in tables_in_order:
        op.drop_table(table)
