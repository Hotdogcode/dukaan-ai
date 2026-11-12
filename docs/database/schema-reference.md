# DukaanAI — Database Schema Reference

This reference documents all 43 tables across the DukaanAI production schema, detailing columns, types, nullability, defaults, constraints, foreign keys, and indexes.

---

## 1. Identity & Business Hierarchy

### `users`
Global platform user registry for store owners, cashiers, and managers.
- `id` (`UUID`, PK, NOT NULL)
- `phone_number` (`VARCHAR(15)`, UNIQUE, NOT NULL, Index) — E.164 mobile number (+91...)
- `email` (`VARCHAR(255)`, NULL, Index) — Optional merchant email
- `full_name` (`VARCHAR(120)`, NOT NULL)
- `hashed_password` (`VARCHAR(255)`, NOT NULL)
- `user_status` (`VARCHAR(20)`, NOT NULL, Default: `'ACTIVE'`) — `ACTIVE`, `SUSPENDED`, `DEACTIVATED`
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `refresh_sessions`
JWT refresh token rotation tracking for persistent mobile sessions.
- `id` (`UUID`, PK, NOT NULL)
- `user_id` (`UUID`, FK `users.id` ON DELETE CASCADE, NOT NULL, Index)
- `refresh_token_hash` (`VARCHAR(255)`, UNIQUE, NOT NULL, Index)
- `device_fingerprint` (`VARCHAR(150)`, NULL)
- `ip_address` (`VARCHAR(45)`, NULL)
- `user_agent` (`VARCHAR(255)`, NULL)
- `expires_at` (`TIMESTAMPTZ`, NOT NULL)
- `is_revoked` (`BOOLEAN`, NOT NULL, Default: `false`)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `businesses`
Multi-tenant root organization entity owning one or more retail stores.
- `id` (`UUID`, PK, NOT NULL)
- `legal_name` (`VARCHAR(150)`, NOT NULL)
- `trade_name` (`VARCHAR(150)`, NOT NULL)
- `business_type` (`VARCHAR(50)`, NOT NULL, Default: `'KIRANA'`)
- `gstin` (`VARCHAR(15)`, NULL, Index) — Indian GST Identification Number
- `pan` (`VARCHAR(10)`, NULL)
- `primary_currency` (`VARCHAR(3)`, NOT NULL, Default: `'INR'`)
- `timezone` (`VARCHAR(50)`, NOT NULL, Default: `'Asia/Kolkata'`)
- `preferred_language` (`VARCHAR(10)`, NOT NULL, Default: `'hi'`) — `hi`, `en`, `hinglish`
- `subscription_tier` (`VARCHAR(30)`, NOT NULL, Default: `'FREE'`)
- `is_active` (`BOOLEAN`, NOT NULL, Default: `true`)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `business_users`
Tenant membership association defining user roles and permissions per business.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `user_id` (`UUID`, FK `users.id` ON DELETE CASCADE, NOT NULL)
- `role` (`VARCHAR(30)`, NOT NULL) — `OWNER`, `MANAGER`, `CASHIER`, `AUDITOR`
- `membership_status` (`VARCHAR(20)`, NOT NULL, Default: `'ACTIVE'`) — `INVITED`, `ACTIVE`, `DISABLED`
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `UNIQUE (business_id, user_id)`

### `stores`
Physical or virtual retail storefronts operated by a business.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_code` (`VARCHAR(30)`, NOT NULL)
- `store_name` (`VARCHAR(120)`, NOT NULL)
- `address_line1` (`VARCHAR(255)`, NULL)
- `city` (`VARCHAR(100)`, NULL)
- `state` (`VARCHAR(100)`, NULL)
- `pincode` (`VARCHAR(10)`, NULL)
- `phone_number` (`VARCHAR(15)`, NULL)
- `is_active` (`BOOLEAN`, NOT NULL, Default: `true`)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `UNIQUE (business_id, store_code)`

---

## 2. Product Catalogue

### `units_of_measure`
Global and domain standard units of measure (e.g. PCS, KG, GM, L, ML).
- `id` (`UUID`, PK, NOT NULL)
- `code` (`VARCHAR(20)`, UNIQUE, NOT NULL, Index) — `PCS`, `KG`, `GM`, `L`, `ML`
- `name` (`VARCHAR(50)`, NOT NULL)
- `category` (`VARCHAR(20)`, NOT NULL) — `COUNT`, `MASS`, `VOLUME`
- `is_fractional_allowed` (`BOOLEAN`, NOT NULL, Default: `true`)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `categories`
Hierarchical product categorization taxonomy.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `name` (`VARCHAR(80)`, NOT NULL)
- `description` (`VARCHAR(255)`, NULL)
- `parent_id` (`UUID`, FK `categories.id` ON DELETE SET NULL, NULL)
- `is_active` (`BOOLEAN`, NOT NULL, Default: `true`)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `UNIQUE (business_id, name)`

### `products`
Master catalog definition of SKUs, pricing, MRP, and tax rates.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `category_id` (`UUID`, FK `categories.id` ON DELETE SET NULL, NULL, Index)
- `name` (`VARCHAR(200)`, NOT NULL, Index)
- `sku` (`VARCHAR(60)`, NOT NULL, Index)
- `hsn_code` (`VARCHAR(20)`, NULL)
- `base_uom_id` (`UUID`, FK `units_of_measure.id` ON DELETE RESTRICT, NOT NULL)
- `selling_price` (`NUMERIC(14, 2)`, NOT NULL)
- `mrp` (`NUMERIC(14, 2)`, NOT NULL)
- `cost_price` (`NUMERIC(14, 4)`, NOT NULL, Default: `0.0000`)
- `tax_rate_percent` (`NUMERIC(5, 2)`, NOT NULL, Default: `0.00`)
- `is_tax_inclusive` (`BOOLEAN`, NOT NULL, Default: `true`)
- `reorder_threshold` (`NUMERIC(14, 4)`, NOT NULL, Default: `0.0000`)
- `is_loose_item` (`BOOLEAN`, NOT NULL, Default: `false`)
- `is_active` (`BOOLEAN`, NOT NULL, Default: `true`)
- `metadata_json` (`JSONB`, NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**:
  - `UNIQUE (business_id, sku)`
  - `CHECK (selling_price <= mrp)` (`chk_selling_price_le_mrp`)
  - `CHECK (selling_price >= 0)` (`chk_selling_price_non_negative`)
  - `CHECK (mrp >= 0)` (`chk_mrp_non_negative`)
  - `CHECK (tax_rate_percent >= 0 AND tax_rate_percent <= 100)` (`chk_tax_rate_percent_range`)

### `product_barcodes`
Mapping of 1D/2D EAN/UPC barcodes to products.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `product_id` (`UUID`, FK `products.id` ON DELETE CASCADE, NOT NULL, Index)
- `barcode` (`VARCHAR(60)`, NOT NULL, Index)
- `is_primary` (`BOOLEAN`, NOT NULL, Default: `true`)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `UNIQUE (business_id, barcode)`

### `unit_conversions`
Product-specific conversion multipliers between pack units and base UOM.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `product_id` (`UUID`, FK `products.id` ON DELETE CASCADE, NOT NULL, Index)
- `from_uom_id` (`UUID`, FK `units_of_measure.id` ON DELETE RESTRICT, NOT NULL)
- `to_uom_id` (`UUID`, FK `units_of_measure.id` ON DELETE RESTRICT, NOT NULL)
- `multiplier` (`NUMERIC(14, 4)`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**:
  - `UNIQUE (product_id, from_uom_id, to_uom_id)`
  - `CHECK (multiplier > 0)` (`chk_conversion_multiplier_positive`)

---

## 3. Sales Management

### `sales`
POS sales transaction invoices.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `customer_id` (`UUID`, FK `customers.id` ON DELETE SET NULL, NULL, Index)
- `cashier_user_id` (`UUID`, FK `users.id` ON DELETE RESTRICT, NOT NULL, Index)
- `invoice_number` (`VARCHAR(50)`, NOT NULL, Index)
- `status` (`VARCHAR(30)`, NOT NULL, Default: `'COMPLETED'`) — `DRAFT`, `COMPLETED`, `PARTIALLY_PAID`, `RETURNED`, `VOIDED`
- `subtotal_amount` (`NUMERIC(14, 2)`, NOT NULL)
- `discount_amount` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`)
- `tax_amount` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`)
- `total_amount` (`NUMERIC(14, 2)`, NOT NULL)
- `paid_amount` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`)
- `credit_amount` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`)
- `occurred_at` (`TIMESTAMPTZ`, NOT NULL, Index)
- `client_created_at` (`TIMESTAMPTZ`, NOT NULL)
- `synced_at` (`TIMESTAMPTZ`, NULL)
- `notes` (`VARCHAR(255)`, NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**:
  - `UNIQUE (store_id, invoice_number)`
  - `CHECK (total_amount >= 0)`
  - `CHECK (paid_amount >= 0)`
  - `CHECK (credit_amount >= 0)`

### `sale_items`
Individual line items sold in a sale invoice.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `sale_id` (`UUID`, FK `sales.id` ON DELETE CASCADE, NOT NULL, Index)
- `product_id` (`UUID`, FK `products.id` ON DELETE RESTRICT, NOT NULL, Index)
- `uom_id` (`UUID`, FK `units_of_measure.id` ON DELETE RESTRICT, NOT NULL)
- `quantity` (`NUMERIC(14, 4)`, NOT NULL)
- `unit_price` (`NUMERIC(14, 2)`, NOT NULL)
- `unit_cost_basis` (`NUMERIC(14, 4)`, NOT NULL, Default: `0.0000`)
- `discount_amount` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`)
- `tax_amount` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`)
- `line_total` (`NUMERIC(14, 2)`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**:
  - `CHECK (quantity > 0)` (`chk_sale_item_quantity_positive`)
  - `CHECK (unit_price >= 0)` (`chk_sale_item_price_non_negative`)

### `sale_returns`
Header for goods returned by customers.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `original_sale_id` (`UUID`, FK `sales.id` ON DELETE RESTRICT, NOT NULL, Index)
- `processed_by_user_id` (`UUID`, FK `users.id` ON DELETE RESTRICT, NOT NULL)
- `return_number` (`VARCHAR(50)`, UNIQUE, NOT NULL)
- `refund_amount` (`NUMERIC(14, 2)`, NOT NULL)
- `refund_method` (`VARCHAR(30)`, NOT NULL) — `CASH`, `UPI`, `CUSTOMER_CREDIT`
- `reason` (`VARCHAR(255)`, NOT NULL)
- `occurred_at` (`TIMESTAMPTZ`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `sale_return_items`
Returned line items with restock eligibility flags.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `sale_return_id` (`UUID`, FK `sale_returns.id` ON DELETE CASCADE, NOT NULL, Index)
- `original_sale_item_id` (`UUID`, FK `sale_items.id` ON DELETE RESTRICT, NOT NULL)
- `product_id` (`UUID`, FK `products.id` ON DELETE RESTRICT, NOT NULL)
- `quantity_returned` (`NUMERIC(14, 4)`, NOT NULL)
- `refund_unit_price` (`NUMERIC(14, 2)`, NOT NULL)
- `refund_line_total` (`NUMERIC(14, 2)`, NOT NULL)
- `is_restockable` (`BOOLEAN`, NOT NULL, Default: `true`)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `CHECK (quantity_returned > 0)` (`chk_sale_return_qty_positive`)

### `sale_reversals`
Full audit reversal for erroneous sales transactions.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `original_sale_id` (`UUID`, FK `sales.id` ON DELETE RESTRICT, UNIQUE, NOT NULL)
- `authorized_by_user_id` (`UUID`, FK `users.id` ON DELETE RESTRICT, NOT NULL)
- `reversal_reason` (`VARCHAR(255)`, NOT NULL)
- `occurred_at` (`TIMESTAMPTZ`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

---

## 4. Purchasing & Suppliers

### `suppliers`
Wholesale supplier directory and credit balance tracking.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `name` (`VARCHAR(150)`, NOT NULL, Index)
- `phone_number` (`VARCHAR(15)`, NOT NULL, Index)
- `gstin` (`VARCHAR(15)`, NULL)
- `payment_terms_days` (`INTEGER`, NOT NULL, Default: `0`)
- `current_balance` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`) — Positive = merchant owes supplier
- `is_active` (`BOOLEAN`, NOT NULL, Default: `true`)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `UNIQUE (business_id, gstin)`

### `purchases`
Wholesale inventory inward bills.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `supplier_id` (`UUID`, FK `suppliers.id` ON DELETE RESTRICT, NOT NULL, Index)
- `invoice_number` (`VARCHAR(80)`, NOT NULL)
- `status` (`VARCHAR(30)`, NOT NULL, Default: `'RECEIVED'`) — `ORDERED`, `RECEIVED`, `PARTIALLY_PAID`, `PAID`, `CANCELLED`
- `subtotal_amount` (`NUMERIC(14, 2)`, NOT NULL)
- `tax_amount` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`)
- `total_amount` (`NUMERIC(14, 2)`, NOT NULL)
- `paid_amount` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`)
- `credit_amount` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`)
- `received_at` (`TIMESTAMPTZ`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `UNIQUE (supplier_id, invoice_number)`

### `purchase_items`
Line items in wholesale stock receipts.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `purchase_id` (`UUID`, FK `purchases.id` ON DELETE CASCADE, NOT NULL, Index)
- `product_id` (`UUID`, FK `products.id` ON DELETE RESTRICT, NOT NULL, Index)
- `uom_id` (`UUID`, FK `units_of_measure.id` ON DELETE RESTRICT, NOT NULL)
- `quantity` (`NUMERIC(14, 4)`, NOT NULL)
- `purchase_rate` (`NUMERIC(14, 4)`, NOT NULL)
- `tax_amount` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`)
- `line_total` (`NUMERIC(14, 2)`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**:
  - `CHECK (quantity > 0)` (`chk_purchase_item_qty_positive`)
  - `CHECK (purchase_rate >= 0)` (`chk_purchase_item_rate_non_negative`)

### `purchase_returns`
Wholesale supplier debit notes.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `purchase_id` (`UUID`, FK `purchases.id` ON DELETE RESTRICT, NOT NULL)
- `supplier_id` (`UUID`, FK `suppliers.id` ON DELETE RESTRICT, NOT NULL)
- `debit_note_number` (`VARCHAR(80)`, NOT NULL)
- `total_debit_amount` (`NUMERIC(14, 2)`, NOT NULL)
- `reason` (`VARCHAR(255)`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `purchase_return_items`
Returned stock line items to wholesale vendor.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `purchase_return_id` (`UUID`, FK `purchase_returns.id` ON DELETE CASCADE, NOT NULL, Index)
- `product_id` (`UUID`, FK `products.id` ON DELETE RESTRICT, NOT NULL)
- `quantity_returned` (`NUMERIC(14, 4)`, NOT NULL)
- `unit_cost` (`NUMERIC(14, 4)`, NOT NULL)
- `line_total` (`NUMERIC(14, 2)`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `CHECK (quantity_returned > 0)` (`chk_purchase_return_qty_positive`)

---

## 5. Inventory & Stock Movement Journal

### `stock_movements`
Authoritative, immutable physical inventory movement journal.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `product_id` (`UUID`, FK `products.id` ON DELETE RESTRICT, NOT NULL, Index)
- `movement_type` (`VARCHAR(30)`, NOT NULL) — `PURCHASE_RECEIPT`, `SALE_DEDUCTION`, `SALE_RETURN`, `PURCHASE_RETURN`, `DAMAGE_SPOILAGE`, `AUDIT_ADJUSTMENT`
- `quantity_delta` (`NUMERIC(14, 4)`, NOT NULL) — Signed quantity in BaseUnit (+ for receipt, - for deduction)
- `unit_cost_at_movement` (`NUMERIC(14, 4)`, NULL)
- `balance_after_movement` (`NUMERIC(14, 4)`, NOT NULL)
- `reference_id` (`UUID`, NOT NULL, Index)
- `idempotency_key` (`UUID`, NOT NULL, Index)
- `occurred_at` (`TIMESTAMPTZ`, NOT NULL, Index)
- `created_at` (`TIMESTAMPTZ`, NOT NULL)
- **Constraints**:
  - `UNIQUE (business_id, idempotency_key)` (`uq_stock_movement_idempotency`)
  - `CHECK (quantity_delta != 0)` (`chk_stock_movement_qty_non_zero`)
  - Index: `ix_stock_movements_query (business_id, store_id, product_id, occurred_at)`

### `stock_balances`
Fast projection cache of current stock on hand per store and product.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `product_id` (`UUID`, FK `products.id` ON DELETE RESTRICT, NOT NULL, Index)
- `current_quantity` (`NUMERIC(14, 4)`, NOT NULL, Default: `0.0000`)
- `moving_average_cost` (`NUMERIC(14, 4)`, NOT NULL, Default: `0.0000`)
- `last_movement_id` (`UUID`, FK `stock_movements.id` ON DELETE SET NULL, NULL)
- `version` (`INTEGER`, NOT NULL, Default: `1`) — Optimistic locking token
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**:
  - `UNIQUE (business_id, store_id, product_id)` (`uq_stock_balance_business_store_product`)
  - `CHECK (moving_average_cost >= 0)` (`chk_stock_balance_cost_non_negative`)
  - Index: `ix_stock_balances_lookup (business_id, store_id, product_id)`

### `inventory_count_sessions`
Physical inventory stock-taking audit sessions.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `conducted_by_user_id` (`UUID`, FK `users.id` ON DELETE RESTRICT, NOT NULL)
- `status` (`VARCHAR(30)`, NOT NULL, Default: `'OPEN'`) — `OPEN`, `COMPLETED`, `CANCELLED`
- `notes` (`VARCHAR(255)`, NULL)
- `started_at` (`TIMESTAMPTZ`, NOT NULL)
- `completed_at` (`TIMESTAMPTZ`, NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `inventory_adjustments`
Variance reconciliation adjustments derived from count sessions.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `session_id` (`UUID`, FK `inventory_count_sessions.id` ON DELETE SET NULL, NULL)
- `product_id` (`UUID`, FK `products.id` ON DELETE RESTRICT, NOT NULL)
- `system_quantity` (`NUMERIC(14, 4)`, NOT NULL)
- `counted_quantity` (`NUMERIC(14, 4)`, NOT NULL)
- `variance_quantity` (`NUMERIC(14, 4)`, NOT NULL)
- `reason` (`VARCHAR(255)`, NOT NULL)
- `approved_by_user_id` (`UUID`, FK `users.id` ON DELETE RESTRICT, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

---

## 6. Khata (Customer & Supplier Ledgers)

### `customers`
Customer Khata accounts and credit balance tracking.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `full_name` (`VARCHAR(150)`, NOT NULL, Index)
- `phone_number` (`VARCHAR(15)`, NOT NULL, Index)
- `credit_limit` (`NUMERIC(14, 2)`, NULL)
- `current_balance` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`) — Positive = customer owes store; Negative = advance deposit
- `is_active` (`BOOLEAN`, NOT NULL, Default: `true`)
- `notes` (`VARCHAR(255)`, NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `UNIQUE (business_id, phone_number)` (`uq_customer_business_phone`)

### `customer_ledger_entries`
Immutable log of credit sales, repayments, and balance adjustments.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `customer_id` (`UUID`, FK `customers.id` ON DELETE CASCADE, NOT NULL, Index)
- `entry_type` (`VARCHAR(30)`, NOT NULL) — `CREDIT_SALE_DEBIT`, `PAYMENT_CREDIT`, `ADJUSTMENT_DEBIT`, `ADJUSTMENT_CREDIT`, `ADVANCE_DEPOSIT`
- `amount` (`NUMERIC(14, 2)`, NOT NULL)
- `running_balance` (`NUMERIC(14, 2)`, NOT NULL)
- `reference_id` (`UUID`, NULL, Index)
- `notes` (`VARCHAR(255)`, NULL)
- `occurred_at` (`TIMESTAMPTZ`, NOT NULL, Index)
- `created_at` (`TIMESTAMPTZ`, NOT NULL)
- **Constraints**:
  - `CHECK (amount > 0)` (`chk_cle_amount_positive`)
  - Index: `ix_customer_ledger_timeline (business_id, customer_id, occurred_at)`

### `customer_payment_allocations`
Maps repayments to previous unpaid credit sales.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `customer_id` (`UUID`, FK `customers.id` ON DELETE CASCADE, NOT NULL, Index)
- `payment_id` (`UUID`, FK `payments.id` ON DELETE RESTRICT, NOT NULL, Index)
- `sale_id` (`UUID`, FK `sales.id` ON DELETE SET NULL, NULL, Index)
- `allocated_amount` (`NUMERIC(14, 2)`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `supplier_ledger_entries`
Wholesale ledger tracking purchase liabilities and vendor payouts.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `supplier_id` (`UUID`, FK `suppliers.id` ON DELETE CASCADE, NOT NULL, Index)
- `entry_type` (`VARCHAR(30)`, NOT NULL) — `PURCHASE_LIABILITY_CREDIT`, `SETTLEMENT_PAYMENT_DEBIT`, `DEBIT_NOTE_ADJUSTMENT`
- `amount` (`NUMERIC(14, 2)`, NOT NULL)
- `running_balance` (`NUMERIC(14, 2)`, NOT NULL)
- `reference_id` (`UUID`, NULL, Index)
- `notes` (`VARCHAR(255)`, NULL)
- `occurred_at` (`TIMESTAMPTZ`, NOT NULL, Index)
- `created_at` (`TIMESTAMPTZ`, NOT NULL)
- **Constraints**:
  - `CHECK (amount > 0)` (`chk_sle_amount_positive`)
  - Index: `ix_supplier_ledger_timeline (business_id, supplier_id, occurred_at)`

### `supplier_payment_allocations`
Maps payout payments to specific supplier purchase bills.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `supplier_id` (`UUID`, FK `suppliers.id` ON DELETE CASCADE, NOT NULL, Index)
- `purchase_id` (`UUID`, FK `purchases.id` ON DELETE RESTRICT, NOT NULL, Index)
- `payment_id` (`UUID`, FK `payments.id` ON DELETE RESTRICT, NOT NULL, Index)
- `allocated_amount` (`NUMERIC(14, 2)`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

---

## 7. Financial Management & Cash Drawer

### `cash_registers`
Shift session management and cash drawer (Galla) reconciliation.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `opened_by_user_id` (`UUID`, FK `users.id` ON DELETE RESTRICT, NOT NULL)
- `closed_by_user_id` (`UUID`, FK `users.id` ON DELETE RESTRICT, NULL)
- `opening_float` (`NUMERIC(14, 2)`, NOT NULL, Default: `0.00`)
- `expected_closing_cash` (`NUMERIC(14, 2)`, NULL)
- `actual_closing_cash` (`NUMERIC(14, 2)`, NULL)
- `variance` (`NUMERIC(14, 2)`, NULL)
- `status` (`VARCHAR(20)`, NOT NULL, Default: `'OPEN'`) — `OPEN`, `CLOSED`
- `notes` (`VARCHAR(255)`, NULL)
- `opened_at` (`TIMESTAMPTZ`, NOT NULL)
- `closed_at` (`TIMESTAMPTZ`, NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `expenses`
Direct operating expenses paid out from store cash or UPI.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `recorded_by_user_id` (`UUID`, FK `users.id` ON DELETE RESTRICT, NOT NULL)
- `cash_register_id` (`UUID`, FK `cash_registers.id` ON DELETE SET NULL, NULL)
- `category` (`VARCHAR(50)`, NOT NULL) — `RENT`, `ELECTRICITY`, `SALARY`, `MAINTENANCE`, `LOGISTICS`, `REFRESHMENTS`, `OTHER`
- `amount` (`NUMERIC(14, 2)`, NOT NULL)
- `payment_method` (`VARCHAR(30)`, NOT NULL) — `CASH`, `UPI`, `BANK_TRANSFER`
- `recipient_name` (`VARCHAR(150)`, NULL)
- `notes` (`VARCHAR(255)`, NULL)
- `occurred_at` (`TIMESTAMPTZ`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `CHECK (amount > 0)` (`chk_expense_amount_positive`)

### `payments`
Unified payment tender ledger across Sales, Khata Repayments, and Payouts.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `payment_type` (`VARCHAR(30)`, NOT NULL) — `CUSTOMER_SALE`, `CUSTOMER_KHATA_REPAYMENT`, `SUPPLIER_PURCHASE_PAYOUT`, `EXPENSE_PAYOUT`
- `payment_method` (`VARCHAR(30)`, NOT NULL) — `CASH`, `UPI`, `BANK_TRANSFER`, `CUSTOMER_CREDIT`
- `amount` (`NUMERIC(14, 2)`, NOT NULL)
- `status` (`VARCHAR(30)`, NOT NULL, Default: `'SETTLED'`) — `PENDING`, `SETTLED`, `FAILED`, `REFUNDED`, `REVERSED`
- `transaction_reference` (`VARCHAR(120)`, NULL)
- `cash_register_id` (`UUID`, FK `cash_registers.id` ON DELETE SET NULL, NULL)
- `occurred_at` (`TIMESTAMPTZ`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `CHECK (amount > 0)` (`chk_payment_amount_positive`)

### `payment_allocations`
Maps payments to their operational targets.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `payment_id` (`UUID`, FK `payments.id` ON DELETE CASCADE, NOT NULL, Index)
- `target_type` (`VARCHAR(30)`, NOT NULL) — `SALE`, `PURCHASE`, `CUSTOMER_ACCOUNT`, `EXPENSE`
- `target_id` (`UUID`, NOT NULL, Index)
- `allocated_amount` (`NUMERIC(14, 2)`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `cash_movements`
Shift audit log of all drawer inflows and outflows.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `cash_register_id` (`UUID`, FK `cash_registers.id` ON DELETE CASCADE, NOT NULL, Index)
- `movement_type` (`VARCHAR(30)`, NOT NULL) — `FLOAT_IN`, `SALE_IN`, `KHATA_REPAYMENT_IN`, `EXPENSE_OUT`, `SUPPLIER_PAYOUT_OUT`, `FLOAT_OUT`
- `amount` (`NUMERIC(14, 2)`, NOT NULL)
- `notes` (`VARCHAR(255)`, NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL)
- **Constraints**: `CHECK (amount > 0)` (`chk_cm_amount_positive`)

---

## 8. Events, Audit & Offline Synchronization

### `business_events`
Transactional outbox publishing domain events for async subscribers.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE SET NULL, NULL)
- `aggregate_id` (`UUID`, NOT NULL, Index)
- `aggregate_type` (`VARCHAR(50)`, NOT NULL, Index)
- `event_name` (`VARCHAR(80)`, NOT NULL, Index)
- `event_version` (`INTEGER`, NOT NULL, Default: `1`)
- `payload_json` (`JSONB`, NOT NULL)
- `occurred_at` (`TIMESTAMPTZ`, NOT NULL, Index)
- `created_at` (`TIMESTAMPTZ`, NOT NULL)

### `audit_logs`
Immutable compliance and security access audit trail.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `user_id` (`UUID`, FK `users.id` ON DELETE SET NULL, NULL, Index)
- `action` (`VARCHAR(50)`, NOT NULL, Index)
- `entity_name` (`VARCHAR(50)`, NOT NULL, Index)
- `entity_id` (`UUID`, NOT NULL, Index)
- `old_values` (`JSONB`, NULL)
- `new_values` (`JSONB`, NULL)
- `ip_address` (`VARCHAR(45)`, NULL)
- `user_agent` (`VARCHAR(255)`, NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Index)

### `idempotency_keys`
API request deduplication preventing double-submits.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `idempotency_key` (`VARCHAR(100)`, NOT NULL)
- `request_path` (`VARCHAR(255)`, NOT NULL)
- `response_code` (`INTEGER`, NOT NULL)
- `response_body` (`JSONB`, NOT NULL)
- `expires_at` (`TIMESTAMPTZ`, NOT NULL, Index)
- `created_at` (`TIMESTAMPTZ`, NOT NULL)
- **Constraints**: `UNIQUE (business_id, idempotency_key)`

### `device_registrations`
User mobile terminal registrations for push notifications and authorization.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `user_id` (`UUID`, FK `users.id` ON DELETE CASCADE, NOT NULL, Index)
- `device_name` (`VARCHAR(100)`, NOT NULL)
- `fcm_token` (`VARCHAR(255)`, NULL)
- `is_trusted` (`BOOLEAN`, NOT NULL, Default: `true`)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `sync_devices`
Store POS counter hardware fingerprint registration and sync watermarks.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `device_fingerprint` (`VARCHAR(150)`, NOT NULL, Index)
- `device_name` (`VARCHAR(100)`, NOT NULL)
- `app_version` (`VARCHAR(30)`, NOT NULL)
- `last_synced_at` (`TIMESTAMPTZ`, NULL)
- `is_active` (`BOOLEAN`, NOT NULL, Default: `true`)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- **Constraints**: `UNIQUE (business_id, device_fingerprint)`

### `sync_operations`
Log of client-generated offline mutations pushed to the server.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `device_id` (`UUID`, FK `sync_devices.id` ON DELETE CASCADE, NOT NULL, Index)
- `operation_id` (`UUID`, NOT NULL, Index)
- `operation_type` (`VARCHAR(50)`, NOT NULL)
- `aggregate_id` (`UUID`, NOT NULL)
- `status` (`VARCHAR(30)`, NOT NULL, Default: `'QUEUED'`) — `QUEUED`, `PROCESSED`, `REJECTED`, `CONFLICT_RESOLVED`
- `error_message` (`VARCHAR(255)`, NULL)
- `client_occurred_at` (`TIMESTAMPTZ`, NOT NULL)
- `server_processed_at` (`TIMESTAMPTZ`, NULL)
- `payload_json` (`JSONB`, NOT NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL)
- **Constraints**: `UNIQUE (device_id, operation_id)`

---

## 9. AI Assistant (DukaanAI)

### `ai_conversations`
Merchant conversational chat sessions.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `store_id` (`UUID`, FK `stores.id` ON DELETE RESTRICT, NOT NULL)
- `user_id` (`UUID`, FK `users.id` ON DELETE RESTRICT, NOT NULL, Index)
- `session_title` (`VARCHAR(120)`, NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `ai_messages`
Turn-by-turn conversational utterances and LLM interpretations.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `conversation_id` (`UUID`, FK `ai_conversations.id` ON DELETE CASCADE, NOT NULL, Index)
- `sender_type` (`VARCHAR(20)`, NOT NULL) — `USER`, `ASSISTANT`, `SYSTEM`
- `raw_utterance` (`TEXT`, NOT NULL)
- `intent_detected` (`VARCHAR(60)`, NULL)
- `confidence_score` (`NUMERIC(5, 4)`, NULL)
- `structured_payload` (`JSONB`, NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)

### `ai_actions`
Structured action drafts proposed by the assistant awaiting user confirmation.
- `id` (`UUID`, PK, NOT NULL)
- `business_id` (`UUID`, FK `businesses.id` ON DELETE CASCADE, NOT NULL)
- `conversation_id` (`UUID`, FK `ai_conversations.id` ON DELETE CASCADE, NOT NULL, Index)
- `action_type` (`VARCHAR(50)`, NOT NULL) — `RECORD_SALE`, `RECORD_EXPENSE`, `RECORD_PURCHASE`, `CUSTOMER_CREDIT`
- `proposed_payload` (`JSONB`, NOT NULL)
- `status` (`VARCHAR(30)`, NOT NULL, Default: `'PROPOSED'`) — `PROPOSED`, `USER_CONFIRMED`, `USER_REJECTED`, `EXECUTED`, `FAILED`
- `executed_entity_id` (`UUID`, NULL)
- `confirmed_by_user_id` (`UUID`, FK `users.id` ON DELETE SET NULL, NULL)
- `confirmed_at` (`TIMESTAMPTZ`, NULL)
- `created_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
- `updated_at` (`TIMESTAMPTZ`, NOT NULL, Default: `now()`)
