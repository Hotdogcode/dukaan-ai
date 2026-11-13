# Inventory Domain Events & Auditing

## 1. Domain Events Emitted
The inventory lifecycle emits standard structured domain events:
- `StockMovementRecorded`: Triggered when an immutable ledger movement is appended.
- `StockCountCompleted`: Emitted when an audit count session finishes, specifying total items audited and discrepancies resolved.
- `NegativeStockTriggered`: Alert event when an outward transaction brings stock below zero.
- `LowStockThresholdBreached`: Alert event when balance drops below `min_stock_level`.

## 2. Security & Compliance
- **PostgreSQL Row-Level Security (RLS)**: Strictly isolates stock balances and movements by `business_id = current_setting('app.current_tenant_id')`.
- **RBAC Permissions**:
  - `INVENTORY_READ`: View stock levels and reports.
  - `INVENTORY_OPENING_STOCK`: Initial stock entry.
  - `INVENTORY_ADJUST`: Damage, shrinkage, and manual balance adjustment.
  - `INVENTORY_COUNT`: Physical count initiation and completion.
  - `INVENTORY_RECONCILE`: Ledger repair operations (OWNER/ADMIN only).
