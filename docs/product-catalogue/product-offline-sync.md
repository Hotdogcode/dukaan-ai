# Product Offline Caching & Synchronization Architecture

## 1. Offline-First Philosophy
Retail stores frequently experience flaky 4G/5G mobile connectivity. DukaanAI is built so that product cataloguing, inventory browsing, and barcode scanning work with **zero latency** completely offline.

## 2. Architecture: Single Source of Truth
- **Read Path:** The Jetpack Compose UI observes the local Room database (`DukaanDatabase`) via reactive Kotlin `Flow`. It **never** waits for network round-trips to display products, categories, or prices.
- **Write Path:** When a user creates or updates a product:
  1. The product, variant, and barcode are saved immediately into local Room tables.
  2. A sync action record is enqueued in the `catalogue_outbox` table (`CatalogueOutboxEntity`) with `sync_status = "PENDING"`.
  3. If network is available, the repository attempts to push the mutation to the remote API.
  4. Upon remote success, `sync_status` transitions to `SYNCED`. If network fails or is unavailable, the outbox record remains `PENDING` to be dispatched by background sync workers when connectivity resumes.
- **Remote Invalidation / Pull:** When `syncCatalogue(businessId)` is triggered (on app open, dashboard entry, or pull-to-refresh):
  1. Products, categories, brands, and units are fetched from `/api/v1/products`, `/categories`, etc.
  2. Room tables are updated within atomic `@Transaction` boundaries.
  3. UI flows automatically emit the updated snapshots.

## 3. Conflict Resolution
- Client mutations are stamped with local timestamp and outbox IDs.
- Server returns canonical `updated_at` timestamps.
- In subsequent synchronization stages, deterministic last-write-wins (LWW) with server reconciliation handles multi-device concurrent updates.
