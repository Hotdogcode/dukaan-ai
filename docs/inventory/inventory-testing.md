# Inventory Testing Strategy & Verification Report

## 1. Test Layers
DukaanAI inventory features are rigorously tested across both backend and mobile client:

### Backend Testing (Pytest)
- **Unit & Schema Tests**: Validates 47 database tables, variant-level unique constraints on `stock_balances`, and decimal precision.
- **Integration Tests** (`backend/tests/integration/test_inventory_api.py`):
  - Initial opening stock creation and double-entry prohibition (409 Conflict).
  - WAC recomputation across sequential lot purchases.
  - Manual stock adjustments (damage, shrinkage, found).
  - Physical stock audit session lifecycle with automated `AUDIT_ADJUSTMENT` movement generation.
  - Configurable negative stock policy enforcement (`DISALLOW_NEGATIVE_STOCK` vs `ALLOW_NEGATIVE_STOCK`).
  - Total projection reconciliation and ledger repair.

### Android Testing (JUnit, MockK, Turbine)
- **Data Layer Tests** (`android/core/data/src/test/java/ai/dukaan/core/data/InventoryRepositoryTest.kt`):
  - Local database cache updates on successful API responses.
  - Outbox queueing and offline fallback during network interruptions.
  - Decimal WAC arithmetic verification.
- **UI State & ViewModel Tests** (`android/feature/inventory/src/test/java/ai/dukaan/feature/inventory/InventoryListViewModelTest.kt`):
  - Dynamic search filtering and category chip handling.
  - Mutually exclusive low-stock vs out-of-stock filtering.
  - Flow state observation with Turbine.
