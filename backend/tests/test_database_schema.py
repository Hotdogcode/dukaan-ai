"""
Database Schema, Metadata, Constraint, and Isolation Tests for DukaanAI.

Validates:
1. Metadata registry: Exactly 43 domain tables mapped.
2. Tenant isolation: Every business-scoped entity contains non-nullable `business_id` FK.
3. Store scoping: All physical store entities contain non-nullable `store_id` FK.
4. Primary keys: All entities utilize UUID `id` primary keys.
5. Precision guarantees: Financial fields use NUMERIC(14, 2), quantities/costs NUMERIC(14, 4).
6. Business check constraints: Positive quantities, non-negative amounts, selling_price <= mrp.
7. Indexing and idempotency keys: Required unique indexes and constraints are registered.
8. Concurrency: Optimistic locking version column exists on StockBalance.
9. Session and RLS helper behavior: `set_tenant_context` sets transaction-local configuration.
"""

from decimal import Decimal
import uuid
import pytest
from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from backend.app.infrastructure.database.base import Base
import backend.app.infrastructure.database.models  # Ensures all models are registered
from backend.app.infrastructure.database.models import (
    User,
    Business,
    BusinessUser,
    Store,
    RefreshSession,
    DeviceRegistration,
    Category,
    UnitOfMeasure,
    Product,
    ProductBarcode,
    UnitConversion,
    Sale,
    SaleItem,
    SaleReturn,
    SaleReturnItem,
    SaleReversal,
    Supplier,
    Purchase,
    PurchaseItem,
    PurchaseReturn,
    PurchaseReturnItem,
    StockMovement,
    StockBalance,
    InventoryCountSession,
    InventoryCountItem,
    InventoryAdjustment,
    Customer,
    CustomerLedgerEntry,
    CustomerPaymentAllocation,
    SupplierLedgerEntry,
    SupplierPaymentAllocation,
    CashRegister,
    Expense,
    Payment,
    PaymentAllocation,
    CashMovement,
    BusinessEvent,
    AuditLog,
    IdempotencyKey,
    SyncDevice,
    SyncOperation,
    AIConversation,
    AIMessage,
    AIAction,
)
from backend.app.infrastructure.database.session import set_tenant_context


EXPECTED_TABLES = {
    # Identity & Access (Global/User scoped)
    "users",
    "refresh_sessions",
    # Business & Store hierarchy
    "businesses",
    "business_users",
    "stores",
    # Catalogue
    "categories",
    "brands",
    "units_of_measure",
    "products",
    "product_variants",
    "product_barcodes",
    "unit_conversions",
    "standard_unit_conversions",
    # Sales
    "sales",
    "sale_items",
    "sale_returns",
    "sale_return_items",
    "sale_reversals",
    # Purchasing
    "suppliers",
    "purchases",
    "purchase_items",
    "purchase_returns",
    "purchase_return_items",
    # Inventory
    "stock_movements",
    "stock_balances",
    "inventory_count_sessions",
    "inventory_count_items",
    "inventory_adjustments",
    # Customer Ledger (Khata)
    "customers",
    "customer_ledger_entries",
    "customer_payment_allocations",
    # Supplier Ledger (Khata)
    "supplier_ledger_entries",
    "supplier_payment_allocations",
    # Finance & Cash
    "cash_registers",
    "expenses",
    "payments",
    "payment_allocations",
    "cash_movements",
    # Events & Audit
    "business_events",
    "audit_logs",
    "idempotency_keys",
    # Synchronization
    "device_registrations",
    "sync_devices",
    "sync_operations",
    # AI Assistant
    "ai_conversations",
    "ai_messages",
    "ai_actions",
}

# Standard reference and global tables that do not require business tenant isolation
GLOBAL_TABLES = {"users", "refresh_sessions", "businesses", "units_of_measure", "standard_unit_conversions"}


def test_all_expected_tables_are_registered():
    """Verify all 47 tables are present in Base.metadata."""
    registered = set(Base.metadata.tables.keys())
    assert registered == EXPECTED_TABLES, f"Missing: {EXPECTED_TABLES - registered}, Extra: {registered - EXPECTED_TABLES}"
    assert len(registered) == 47


def test_primary_keys_are_uuid():
    """Verify every table has a single UUID primary key named 'id'."""
    for table_name, table in Base.metadata.tables.items():
        assert "id" in table.columns, f"Table {table_name} missing 'id' column"
        col = table.columns["id"]
        assert col.primary_key, f"Column 'id' on table {table_name} must be a primary key"
        assert isinstance(col.type, UUID) or "UUID" in str(col.type).upper(), (
            f"Table {table_name}.id must be UUID type, got {col.type}"
        )


def test_tenant_isolation_columns_and_foreign_keys():
    """Verify all 39 business-scoped tables have non-nullable business_id referencing businesses.id."""
    for table_name, table in Base.metadata.tables.items():
        if table_name in GLOBAL_TABLES:
            continue
        assert "business_id" in table.columns, f"Tenant table {table_name} must contain business_id"
        col = table.columns["business_id"]
        assert not col.nullable, f"Table {table_name}.business_id must NOT be nullable"

        # Check foreign key to businesses.id
        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "businesses.id" in fk_targets, f"Table {table_name}.business_id must have FK to businesses.id"


def test_store_scoped_tables():
    """Verify store-level operational tables contain non-nullable store_id."""
    store_tables = [
        "sales",
        "sale_returns",
        "purchases",
        "stock_movements",
        "stock_balances",
        "inventory_count_sessions",
        "cash_registers",
        "cash_movements",
        "sync_devices",
    ]
    for table_name in store_tables:
        table = Base.metadata.tables[table_name]
        assert "store_id" in table.columns, f"Operational table {table_name} must contain store_id"
        assert not table.columns["store_id"].nullable, f"Table {table_name}.store_id must not be nullable"
        fk_targets = [fk.target_fullname for fk in table.columns["store_id"].foreign_keys]
        assert "stores.id" in fk_targets, f"Table {table_name}.store_id must have FK to stores.id"


def test_financial_field_precision():
    """Verify strict NUMERIC precision: Money is (14, 2), Quantities/Costs are (14, 4)."""
    # Product prices
    products_table = Base.metadata.tables["products"]
    assert isinstance(products_table.columns["selling_price"].type, Numeric)
    assert products_table.columns["selling_price"].type.precision == 14
    assert products_table.columns["selling_price"].type.scale == 2

    assert isinstance(products_table.columns["mrp"].type, Numeric)
    assert products_table.columns["mrp"].type.scale == 2

    assert isinstance(products_table.columns["cost_price"].type, Numeric)
    assert products_table.columns["cost_price"].type.scale == 4

    assert isinstance(products_table.columns["reorder_threshold"].type, Numeric)
    assert products_table.columns["reorder_threshold"].type.scale == 4

    # SaleItem money & quantity
    sale_items = Base.metadata.tables["sale_items"]
    assert sale_items.columns["unit_price"].type.scale == 2
    assert sale_items.columns["line_total"].type.scale == 2
    assert sale_items.columns["quantity"].type.scale == 4
    assert sale_items.columns["unit_cost_basis"].type.scale == 4

    # StockMovement quantity & cost
    stock_movements = Base.metadata.tables["stock_movements"]
    assert stock_movements.columns["quantity_delta"].type.scale == 4
    assert stock_movements.columns["unit_cost_at_movement"].type.scale == 4
    assert stock_movements.columns["balance_after_movement"].type.scale == 4

    # StockBalance quantity & moving average cost
    stock_balances = Base.metadata.tables["stock_balances"]
    assert stock_balances.columns["current_quantity"].type.scale == 4
    assert stock_balances.columns["moving_average_cost"].type.scale == 4


def test_business_check_constraints():
    """Verify critical business check constraints are declared in table metadata."""
    # Product constraints
    products = Base.metadata.tables["products"]
    chk_names = {c.name for c in products.constraints if isinstance(c, CheckConstraint)}
    assert "chk_selling_price_le_mrp" in chk_names
    assert "chk_selling_price_non_negative" in chk_names
    assert "chk_mrp_non_negative" in chk_names
    assert "chk_tax_rate_percent_range" in chk_names

    # SaleItem constraints
    sale_items = Base.metadata.tables["sale_items"]
    si_chks = {c.name for c in sale_items.constraints if isinstance(c, CheckConstraint)}
    assert "chk_sale_item_quantity_positive" in si_chks
    assert "chk_sale_item_price_non_negative" in si_chks

    # StockMovement constraints
    stock_movements = Base.metadata.tables["stock_movements"]
    sm_chks = {c.name for c in stock_movements.constraints if isinstance(c, CheckConstraint)}
    assert "chk_stock_movement_qty_non_zero" in sm_chks

    # StockBalance constraints
    stock_balances = Base.metadata.tables["stock_balances"]
    sb_chks = {c.name for c in stock_balances.constraints if isinstance(c, CheckConstraint)}
    assert "chk_stock_balance_cost_non_negative" in sb_chks

    # CustomerLedgerEntry constraints
    customer_ledger = Base.metadata.tables["customer_ledger_entries"]
    cle_chks = {c.name for c in customer_ledger.constraints if isinstance(c, CheckConstraint)}
    assert "chk_cle_amount_positive" in cle_chks

    # CashMovement constraints
    cash_movements = Base.metadata.tables["cash_movements"]
    cm_chks = {c.name for c in cash_movements.constraints if isinstance(c, CheckConstraint)}
    assert "chk_cm_amount_positive" in cm_chks


def test_unique_constraints_and_idempotency_keys():
    """Verify unique business indexes and idempotency keys."""
    # StockMovement idempotency key uniqueness
    stock_movements = Base.metadata.tables["stock_movements"]
    sm_uniques = [
        c for c in stock_movements.constraints if isinstance(c, UniqueConstraint)
    ] + [idx for idx in stock_movements.indexes if idx.unique]
    sm_cols_sets = [{col.name for col in u.columns} for u in sm_uniques]
    assert {"business_id", "idempotency_key"} in sm_cols_sets

    # IdempotencyKey table
    idempotency_table = Base.metadata.tables["idempotency_keys"]
    ik_uniques = [
        c for c in idempotency_table.constraints if isinstance(c, UniqueConstraint)
    ] + [idx for idx in idempotency_table.indexes if idx.unique]
    ik_cols_sets = [{col.name for col in u.columns} for u in ik_uniques]
    assert {"business_id", "idempotency_key"} in ik_cols_sets

    # Customer phone per business
    customers = Base.metadata.tables["customers"]
    cust_uniques = [
        c for c in customers.constraints if isinstance(c, UniqueConstraint)
    ] + [idx for idx in customers.indexes if idx.unique]
    cust_cols_sets = [{col.name for col in u.columns} for u in cust_uniques]
    assert {"business_id", "phone_number"} in cust_cols_sets

    # StockBalance store + variant per business
    stock_balances = Base.metadata.tables["stock_balances"]
    sb_uniques = [
        c for c in stock_balances.constraints if isinstance(c, UniqueConstraint)
    ] + [idx for idx in stock_balances.indexes if idx.unique]
    sb_cols_sets = [{col.name for col in u.columns} for u in sb_uniques]
    assert {"business_id", "store_id", "variant_id"} in sb_cols_sets


def test_optimistic_locking_version_column():
    """Verify StockBalance has optimistic concurrency version column."""
    stock_balances = Base.metadata.tables["stock_balances"]
    assert "version" in stock_balances.columns
    assert stock_balances.columns["version"].nullable is False


def test_tenant_context_helper():
    """Verify set_tenant_context produces valid parameterized execution."""
    tenant_id = uuid.uuid4()

    class MockSession:
        def __init__(self):
            self.executed_statements = []

        def execute(self, statement, params=None):
            self.executed_statements.append((str(statement), params))

    mock = MockSession()
    set_tenant_context(mock, tenant_id)
    assert len(mock.executed_statements) == 1
    stmt, params = mock.executed_statements[0]
    assert "SET LOCAL app.current_tenant_id" in stmt
    assert params == {"tenant_id": str(tenant_id)}


def test_alembic_migration_script_contains_rls_policies():
    """Verify Alembic migration scripts define RLS policies on all tenant tables."""
    import importlib
    mig_001 = importlib.import_module("backend.migrations.versions.20261112_001_initial_database_schema")
    mig_003 = importlib.import_module("backend.migrations.versions.20261112_003_add_brands_product_variants_and_catalogue_enhancements")
    mig_004 = importlib.import_module("backend.migrations.versions.20261113_004_enhance_inventory_variant_level_and_stock_ledger")
    tenant_set = set(mig_001.TENANT_TABLES) | set(mig_003.TENANT_TABLES) | set(mig_004.TENANT_TABLES)
    expected_tenant_set = EXPECTED_TABLES - GLOBAL_TABLES

    assert tenant_set == expected_tenant_set, (
        f"Missing RLS tables: {expected_tenant_set - tenant_set}, Extra: {tenant_set - expected_tenant_set}"
    )
    assert len(tenant_set) == 42
