# Product Catalogue Testing Strategy & Verification Report

## 1. Multi-Layer Testing Architecture

### Backend Automated Test Suite (`backend/tests`)
Executed via `pytest -v`:
- **Integration Tests (`tests/integration/test_catalogue_api.py`):**
  - Category creation and cycle prevention (`test_create_category_hierarchy_and_cycle_prevention`).
  - Brand creation and duplicate prevention (`test_create_and_list_brands`).
  - Product creation with default variant and barcode (`test_create_product_with_default_variant_and_barcode`).
  - Variant creation and invariant enforcement: verifies that `selling_price > mrp` raises `422/400 BusinessRuleViolation` (`test_product_variant_price_invariant_enforcement`).
  - Barcode lookup (`test_barcode_lookup`).
  - Multi-tenant isolation: verifies that Business B cannot see Business A's products or categories (`test_multi_tenant_catalogue_isolation`).
  - Units of measure and conversions (`test_list_units_of_measure_and_conversions`).
- **Database Schema Verification (`tests/test_database_schema.py`):**
  - Verifies presence of 46 tables including `brands`, `product_variants`, `standard_unit_conversions`.
  - Verifies RLS policies on all 41 tenant tables.
- **Pass Rate:** 40 / 40 passed (100%).

### Android Automated Test Suite
Executed via `./gradlew testDebugUnitTest`:
- **Data Layer Tests (`core/data/src/test/.../CatalogueRepositoryTest.kt`):**
  - Offline-first cache-and-network sync verification.
  - Client-side invariant rejection when `sellingPrice > mrp`.
  - Non-negative price validations (`sellingPrice >= 0`, `purchasePrice >= 0`, `mrp >= 0`).
  - Reactive `Flow` emissions across Room DAOs.
- **Feature Layer Tests (`feature/catalogue/src/test/.../ProductListViewModelTest.kt`):**
  - Search query filtering.
  - Category chip toggle selection.
  - Active-only status filter toggle.
  - Manual pull-to-refresh catalogue sync triggering.

### Physical Device Verification
- Target device: Samsung Galaxy S20 FE 5G (`SM-G781B`, Android 13).
- CameraX & ML Kit Barcode scanning verification on physical camera feed.
- Live backend connection verified against deployed Render cloud service (`https://dukaanai-backend-yx5b.onrender.com/`).
