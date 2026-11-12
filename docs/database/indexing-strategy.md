# DukaanAI — Database Indexing Strategy

## 1. Principles of Index Design

In a retail kirana application, read patterns are heavily skewed toward fast counter lookups, customer phone searches, and daily shift reconciliation, while write patterns demand lightning-fast insertion of POS sales receipts and inventory movements. 

To achieve sub-millisecond query performance without creating excessive write amplification or table bloat, DukaanAI adopts the following indexing principles:

1. **Equality-First, Range-Last (Left-Prefix Rule)**: In composite indexes, columns queried via exact equality (`business_id`, `store_id`, `customer_id`) precede columns queried via inequalities or sorting ranges (`occurred_at`, `created_at`).
2. **Tenant-First Scoping**: Since 99% of queries are scoped to a specific tenant business, composite indexes start with `business_id` to maximize b-tree selectivity and cooperate cleanly with Row-Level Security (RLS).
3. **Covering Unique Constraints**: Where business logic mandates uniqueness (e.g. `(business_id, barcode)` or `(business_id, phone_number)`), unique constraints are backed by unique b-tree indexes that serve double duty as query paths.
4. **Prudent JSONB Indexing**: Raw `JSONB` columns use GIN indexes only when JSON key filtering is frequent. In DukaanAI, structured metadata is extracted into typed relational columns where possible, reserving JSONB for variable payloads.

---

## 2. Critical Query Patterns & Composite Indexes

### A. Sales Reporting & Daily Cash Closure
- **Query Pattern**: Fetch all sales for a store within a date range (e.g., today's shift).
- **Index**:
  ```sql
  CREATE INDEX ix_sales_business_store_occurred 
  ON sales (business_id, store_id, occurred_at);
  ```
- **Rationale**: Filters precisely by tenant and store, and streams chronological records directly from index leaf nodes without full table scans or sorting steps.

### B. Stock Movement Audit Trail
- **Query Pattern**: Reconstruct stock movement history for a specific product at a store ordered by time.
- **Index**:
  ```sql
  CREATE INDEX ix_stock_movements_query 
  ON stock_movements (business_id, store_id, product_id, occurred_at);
  ```
- **Rationale**: Satisfies both the `WHERE product_id = :p AND store_id = :s` predicate and the `ORDER BY occurred_at` clause.

### C. Fast Stock Balance Lookup
- **Query Pattern**: Fetch current on-hand stock and moving average cost during checkout barcode scan.
- **Index**:
  ```sql
  CREATE UNIQUE INDEX uq_stock_balance_business_store_product 
  ON stock_balances (business_id, store_id, product_id);
  ```
- **Rationale**: Single-page index lookup during POS scanning.

### D. Customer Khata Timeline & Statement
- **Query Pattern**: Render customer ledger statement (debits and payments) in chronological order.
- **Index**:
  ```sql
  CREATE INDEX ix_customer_ledger_timeline 
  ON customer_ledger_entries (business_id, customer_id, occurred_at);
  ```
- **Rationale**: Eliminates filesort on statement queries and supports incremental pagination (`WHERE occurred_at < :cursor`).

### E. Supplier Wholesale Ledger Timeline
- **Query Pattern**: Render supplier purchase bills, payments, and balance timeline.
- **Index**:
  ```sql
  CREATE INDEX ix_supplier_ledger_timeline 
  ON supplier_ledger_entries (business_id, supplier_id, occurred_at);
  ```

### F. Barcode POS Scanning
- **Query Pattern**: Look up product SKU instantly when barcode is scanned by laser or camera.
- **Index**:
  ```sql
  CREATE UNIQUE INDEX uq_product_barcode_business 
  ON product_barcodes (business_id, barcode);
  ```
- **Rationale**: Prevents barcode collisions across merchants while enabling instantaneous exact matches.

### G. Customer Phone Search
- **Query Pattern**: Search customer by phone number during credit sale entry.
- **Index**:
  ```sql
  CREATE UNIQUE INDEX uq_customer_business_phone 
  ON customers (business_id, phone_number);
  ```

### H. Offline Sync Ingestion
- **Query Pattern**: Find pending offline operations for a store device ordered by client timestamp.
- **Index**:
  ```sql
  CREATE INDEX ix_sync_operations_device_status 
  ON sync_operations (business_id, device_id, status, client_occurred_at);
  ```

---

## 3. Index Registry Table

| Table | Index Name | Columns | Type / Purpose |
|---|---|---|---|
| `users` | `ix_users_phone_number` | `(phone_number)` | Unique, Login Lookup |
| `refresh_sessions` | `ix_refresh_sessions_token` | `(refresh_token_hash)` | Unique, Session Auth |
| `businesses` | `ix_businesses_gstin` | `(gstin)` | Lookup, Tax Compliance |
| `business_users` | `uq_business_user_membership` | `(business_id, user_id)` | Unique, Access Control |
| `stores` | `uq_store_business_code` | `(business_id, store_code)` | Unique, Multi-store code |
| `categories` | `uq_category_business_name` | `(business_id, name)` | Unique, Category duplicate check |
| `products` | `uq_product_business_sku` | `(business_id, sku)` | Unique, SKU validation |
| `products` | `ix_products_name` | `(name)` | B-tree, Text search |
| `product_barcodes`| `uq_product_barcode_business` | `(business_id, barcode)` | Unique, Fast POS barcode scan |
| `sales` | `uq_sale_store_invoice` | `(store_id, invoice_number)` | Unique, Invoice idempotency |
| `sales` | `ix_sales_business_store_occurred` | `(business_id, store_id, occurred_at)` | Composite, Shift & date analytics |
| `sale_items` | `ix_sale_items_sale_id` | `(sale_id)` | FK B-tree, Line item joins |
| `stock_movements`| `uq_stock_movement_idempotency` | `(business_id, idempotency_key)` | Unique, Mutation idempotency |
| `stock_movements`| `ix_stock_movements_query` | `(business_id, store_id, product_id, occurred_at)`| Composite, Stock ledger replay |
| `stock_balances` | `uq_stock_balance_business_store_product` | `(business_id, store_id, product_id)` | Unique, POS stock check |
| `customers` | `uq_customer_business_phone` | `(business_id, phone_number)` | Unique, Mobile lookup |
| `customer_ledger_entries` | `ix_customer_ledger_timeline` | `(business_id, customer_id, occurred_at)` | Composite, Khata passbook |
| `supplier_ledger_entries` | `ix_supplier_ledger_timeline` | `(business_id, supplier_id, occurred_at)` | Composite, Vendor statement |
| `cash_registers` | `ix_cash_registers_store_status`| `(store_id, status)` | Composite, Active drawer check |
| `sync_operations`| `uq_device_operation` | `(device_id, operation_id)` | Unique, Sync deduplication |
| `idempotency_keys`| `uq_idempotency_business_key`| `(business_id, idempotency_key)` | Unique, Double-submit block |

---

## 4. Maintenance & Monitoring Guidelines

1. **Autovacuum Tuning for Append-Only Tables**:
   Tables like `stock_movements`, `customer_ledger_entries`, and `business_events` receive high insert volumes with zero updates. Autovacuum settings should be tuned to prevent index bloat:
   ```sql
   ALTER TABLE stock_movements SET (
       autovacuum_vacuum_scale_factor = 0.05,
       autovacuum_analyze_scale_factor = 0.02
   );
   ```
2. **Periodic Unused Index Audits**:
   Monitor index usage using `pg_stat_user_indexes`. Indexes with `idx_scan = 0` after 30 days of production traffic must be evaluated for removal to reduce write overhead.
3. **Zero-Downtime Index Additions**:
   Future index migrations on live high-volume tables must use `CREATE INDEX CONCURRENTLY` in separate non-transactional Alembic operations.
