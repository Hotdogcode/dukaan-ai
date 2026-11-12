from backend.app.infrastructure.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin, StoreScopedMixin

# Identity & Business
from backend.app.infrastructure.database.models.identity import User, RefreshSession
from backend.app.infrastructure.database.models.business import Business, BusinessUser, Store

# Product Catalogue
from backend.app.infrastructure.database.models.catalogue import (
    Brand,
    Category,
    UnitOfMeasure,
    StandardUnitConversion,
    Product,
    ProductVariant,
    ProductBarcode,
    UnitConversion,
)

# Sales & Counter POS
from backend.app.infrastructure.database.models.sales import (
    Sale,
    SaleItem,
    SaleReturn,
    SaleReturnItem,
    SaleReversal,
)

# Purchasing & Suppliers
from backend.app.infrastructure.database.models.purchases import (
    Supplier,
    Purchase,
    PurchaseItem,
    PurchaseReturn,
    PurchaseReturnItem,
)

# Inventory & Stock Movements
from backend.app.infrastructure.database.models.inventory import (
    StockMovement,
    StockBalance,
    InventoryCountSession,
    InventoryAdjustment,
)

# Customers & Khata
from backend.app.infrastructure.database.models.customers import (
    Customer,
    CustomerLedgerEntry,
    CustomerPaymentAllocation,
)

# Suppliers & Liabilities
from backend.app.infrastructure.database.models.suppliers import (
    SupplierLedgerEntry,
    SupplierPaymentAllocation,
)

# Financial Management
from backend.app.infrastructure.database.models.finance import (
    CashRegister,
    Expense,
    Payment,
    PaymentAllocation,
    CashMovement,
)

# Events & Audit
from backend.app.infrastructure.database.models.events import (
    BusinessEvent,
    AuditLog,
    IdempotencyKey,
)

# Synchronization & Offline Devices
from backend.app.infrastructure.database.models.synchronization import (
    DeviceRegistration,
    SyncDevice,
    SyncOperation,
)

# AI & Assistant
from backend.app.infrastructure.database.models.intelligence import (
    AIConversation,
    AIMessage,
    AIAction,
)

__all__ = [
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "TenantMixin",
    "StoreScopedMixin",
    # Identity
    "User",
    "RefreshSession",
    "DeviceRegistration",
    # Business
    "Business",
    "BusinessUser",
    "Store",
    # Catalogue
    "Brand",
    "Category",
    "UnitOfMeasure",
    "StandardUnitConversion",
    "Product",
    "ProductVariant",
    "ProductBarcode",
    "UnitConversion",
    # Sales
    "Sale",
    "SaleItem",
    "SaleReturn",
    "SaleReturnItem",
    "SaleReversal",
    # Purchasing
    "Supplier",
    "Purchase",
    "PurchaseItem",
    "PurchaseReturn",
    "PurchaseReturnItem",
    # Inventory
    "StockMovement",
    "StockBalance",
    "InventoryCountSession",
    "InventoryAdjustment",
    # Customers
    "Customer",
    "CustomerLedgerEntry",
    "CustomerPaymentAllocation",
    # Suppliers
    "SupplierLedgerEntry",
    "SupplierPaymentAllocation",
    # Finance
    "CashRegister",
    "Expense",
    "Payment",
    "PaymentAllocation",
    "CashMovement",
    # Events & Audit
    "BusinessEvent",
    "AuditLog",
    "IdempotencyKey",
    # Synchronization
    "SyncDevice",
    "SyncOperation",
    # AI
    "AIConversation",
    "AIMessage",
    "AIAction",
]
