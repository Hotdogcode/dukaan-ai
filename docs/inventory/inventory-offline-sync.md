# Inventory Offline Architecture & Synchronization

## 1. Local Cache Architecture (Room)
The Android client persists full inventory state in Room database (`DukaanDatabase` v3):
- `stock_balances`: Caches store variant balances.
- `stock_movements`: Caches variant movement history.
- `inventory_count_sessions` & `items`: Offline count session management.
- `inventory_outbox`: Reliable background synchronization queue for write operations.

## 2. Outbox Synchronization Mechanism
When the Android device is offline:
1. Write requests (`OPENING_STOCK`, `ADJUSTMENT`, `AUDIT_COUNT`) are persisted locally into `inventory_outbox`.
2. A unique UUID `idempotency_key` is generated at creation time.
3. Upon network reconnection, `InventorySyncWorker` (or repository dispatch) drains the outbox to the backend.
4. Idempotency keys prevent duplicate ledger entries even if network acknowledgments drop.
