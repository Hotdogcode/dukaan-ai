# DukaanAI — Entity-Relationship Diagrams

To ensure visual clarity and avoid oversized monolithic diagrams, the DukaanAI relational schema is partitioned into functional bounded context entity-relationship diagrams.

---

## 1. Identity & Business Hierarchy

```mermaid
erDiagram
    users ||--o{ business_users : "belongs to"
    users ||--o{ refresh_sessions : "has"
    businesses ||--o{ business_users : "has users"
    businesses ||--o{ stores : "owns"

    users {
        uuid id PK
        varchar phone_number UK
        varchar full_name
        varchar hashed_password
        varchar user_status
        timestamptz created_at
    }

    businesses {
        uuid id PK
        varchar legal_name
        varchar trade_name
        varchar business_type
        varchar gstin UK
        varchar primary_currency
        timestamptz created_at
    }

    business_users {
        uuid id PK
        uuid business_id FK
        uuid user_id FK
        varchar role
        varchar membership_status
        timestamptz created_at
    }

    stores {
        uuid id PK
        uuid business_id FK
        varchar store_code
        varchar store_name
        varchar pincode
        boolean is_active
        timestamptz created_at
    }

    refresh_sessions {
        uuid id PK
        uuid user_id FK
        varchar refresh_token_hash UK
        timestamptz expires_at
        boolean is_revoked
    }
```

---

## 2. Product Catalogue Context

```mermaid
erDiagram
    businesses ||--o{ categories : "defines"
    businesses ||--o{ products : "owns"
    categories ||--o{ categories : "sub-category of"
    categories ||--o{ products : "classifies"
    units_of_measure ||--o{ products : "base unit"
    products ||--o{ product_barcodes : "has barcodes"
    products ||--o{ unit_conversions : "has conversions"

    categories {
        uuid id PK
        uuid business_id FK
        varchar name
        uuid parent_id FK
        boolean is_active
    }

    units_of_measure {
        uuid id PK
        varchar code UK
        varchar name
        varchar category
        boolean is_fractional_allowed
    }

    products {
        uuid id PK
        uuid business_id FK
        uuid category_id FK
        uuid base_uom_id FK
        varchar name
        varchar sku UK
        numeric selling_price
        numeric mrp
        numeric cost_price
        numeric tax_rate_percent
        boolean is_tax_inclusive
        numeric reorder_threshold
    }

    product_barcodes {
        uuid id PK
        uuid business_id FK
        uuid product_id FK
        varchar barcode UK
        boolean is_primary
    }

    unit_conversions {
        uuid id PK
        uuid business_id FK
        uuid product_id FK
        uuid from_uom_id FK
        uuid to_uom_id FK
        numeric multiplier
    }
```

---

## 3. Sales & Returns Context

```mermaid
erDiagram
    stores ||--o{ sales : "issues"
    customers ||--o{ sales : "buys"
    users ||--o{ sales : "cashier"
    sales ||--o{ sale_items : "contains"
    products ||--o{ sale_items : "sold item"
    sales ||--o{ sale_returns : "originates return"
    sale_returns ||--o{ sale_return_items : "contains returned"
    sales ||--o{ sale_reversals : "reversal record"

    sales {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid customer_id FK
        uuid cashier_user_id FK
        varchar invoice_number UK
        varchar status
        numeric subtotal_amount
        numeric discount_amount
        numeric tax_amount
        numeric total_amount
        numeric paid_amount
        numeric credit_amount
        timestamptz occurred_at
    }

    sale_items {
        uuid id PK
        uuid business_id FK
        uuid sale_id FK
        uuid product_id FK
        uuid uom_id FK
        numeric quantity
        numeric unit_price
        numeric unit_cost_basis
        numeric discount_amount
        numeric tax_amount
        numeric line_total
    }

    sale_returns {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid original_sale_id FK
        uuid processed_by_user_id FK
        varchar return_number UK
        numeric refund_amount
        varchar refund_method
        varchar reason
        timestamptz occurred_at
    }

    sale_return_items {
        uuid id PK
        uuid business_id FK
        uuid sale_return_id FK
        uuid original_sale_item_id FK
        uuid product_id FK
        numeric quantity_returned
        numeric refund_unit_price
        numeric refund_line_total
        boolean is_restockable
    }

    sale_reversals {
        uuid id PK
        uuid business_id FK
        uuid original_sale_id FK
        uuid authorized_by_user_id FK
        varchar reversal_reason
        timestamptz occurred_at
    }
```

---

## 4. Purchasing & Supplier Context

```mermaid
erDiagram
    businesses ||--o{ suppliers : "manages"
    suppliers ||--o{ purchases : "bills"
    stores ||--o{ purchases : "receives"
    purchases ||--o{ purchase_items : "contains"
    purchases ||--o{ purchase_returns : "debit notes"
    purchase_returns ||--o{ purchase_return_items : "contains returned"

    suppliers {
        uuid id PK
        uuid business_id FK
        varchar name
        varchar phone_number
        varchar gstin
        numeric current_balance
        boolean is_active
    }

    purchases {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid supplier_id FK
        varchar invoice_number
        varchar status
        numeric total_amount
        numeric paid_amount
        numeric credit_amount
        timestamptz received_at
    }

    purchase_items {
        uuid id PK
        uuid business_id FK
        uuid purchase_id FK
        uuid product_id FK
        uuid uom_id FK
        numeric quantity
        numeric purchase_rate
        numeric line_total
    }

    purchase_returns {
        uuid id PK
        uuid business_id FK
        uuid purchase_id FK
        uuid supplier_id FK
        varchar debit_note_number
        numeric total_debit_amount
        varchar reason
    }

    purchase_return_items {
        uuid id PK
        uuid business_id FK
        uuid purchase_return_id FK
        uuid product_id FK
        numeric quantity_returned
        numeric unit_cost
        numeric line_total
    }
```

---

## 5. Inventory & Movements Context

```mermaid
erDiagram
    stores ||--o{ stock_movements : "records"
    stores ||--o{ stock_balances : "caches"
    products ||--o{ stock_movements : "tracks"
    products ||--o{ stock_balances : "holds balance"
    stores ||--o{ inventory_count_sessions : "audits"
    inventory_count_sessions ||--o{ inventory_adjustments : "generates"

    stock_movements {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid product_id FK
        varchar movement_type
        numeric quantity_delta
        numeric unit_cost_at_movement
        numeric balance_after_movement
        uuid reference_id
        uuid idempotency_key UK
        timestamptz occurred_at
    }

    stock_balances {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid product_id FK
        numeric current_quantity
        numeric moving_average_cost
        uuid last_movement_id FK
        integer version
        timestamptz updated_at
    }

    inventory_count_sessions {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid conducted_by_user_id FK
        varchar status
        timestamptz started_at
        timestamptz completed_at
    }

    inventory_adjustments {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid session_id FK
        uuid product_id FK
        numeric system_quantity
        numeric counted_quantity
        numeric variance_quantity
        varchar reason
    }
```

---

## 6. Khata (Customer & Supplier Ledger) Context

```mermaid
erDiagram
    customers ||--o{ customer_ledger_entries : "khata timeline"
    customers ||--o{ customer_payment_allocations : "clears credit"
    suppliers ||--o{ supplier_ledger_entries : "wholesale ledger"
    suppliers ||--o{ supplier_payment_allocations : "clears bills"
    payments ||--o{ customer_payment_allocations : "allocated from"
    payments ||--o{ supplier_payment_allocations : "allocated from"

    customer_ledger_entries {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid customer_id FK
        varchar entry_type
        numeric amount
        numeric running_balance
        uuid reference_id
        timestamptz occurred_at
    }

    customer_payment_allocations {
        uuid id PK
        uuid business_id FK
        uuid customer_id FK
        uuid payment_id FK
        uuid sale_id FK
        numeric allocated_amount
    }

    supplier_ledger_entries {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid supplier_id FK
        varchar entry_type
        numeric amount
        numeric running_balance
        uuid reference_id
        timestamptz occurred_at
    }

    supplier_payment_allocations {
        uuid id PK
        uuid business_id FK
        uuid supplier_id FK
        uuid purchase_id FK
        uuid payment_id FK
        numeric allocated_amount
    }
```

---

## 7. Financial Management & Cash Register Context

```mermaid
erDiagram
    stores ||--o{ cash_registers : "shift drawer"
    cash_registers ||--o{ cash_movements : "audits flow"
    stores ||--o{ expenses : "logs"
    stores ||--o{ payments : "tenders"
    payments ||--o{ payment_allocations : "distributes"

    cash_registers {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid opened_by_user_id FK
        uuid closed_by_user_id FK
        numeric opening_float
        numeric expected_closing_cash
        numeric actual_closing_cash
        numeric variance
        varchar status
        timestamptz opened_at
        timestamptz closed_at
    }

    cash_movements {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid cash_register_id FK
        varchar movement_type
        numeric amount
        varchar notes
        timestamptz created_at
    }

    expenses {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid recorded_by_user_id FK
        uuid cash_register_id FK
        varchar category
        numeric amount
        varchar payment_method
        timestamptz occurred_at
    }

    payments {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        varchar payment_type
        varchar payment_method
        numeric amount
        varchar status
        uuid cash_register_id FK
        timestamptz occurred_at
    }

    payment_allocations {
        uuid id PK
        uuid business_id FK
        uuid payment_id FK
        varchar target_type
        uuid target_id
        numeric allocated_amount
    }
```

---

## 8. Offline Synchronization & AI Assistant Context

```mermaid
erDiagram
    users ||--o{ device_registrations : "registers"
    stores ||--o{ sync_devices : "hardware counter"
    sync_devices ||--o{ sync_operations : "pushes offline ops"
    stores ||--o{ ai_conversations : "chats"
    ai_conversations ||--o{ ai_messages : "turns"
    ai_conversations ||--o{ ai_actions : "proposes"

    device_registrations {
        uuid id PK
        uuid business_id FK
        uuid user_id FK
        varchar device_name
        varchar fcm_token
        boolean is_trusted
    }

    sync_devices {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        varchar device_fingerprint UK
        varchar device_name
        varchar app_version
        timestamptz last_synced_at
        boolean is_active
    }

    sync_operations {
        uuid id PK
        uuid business_id FK
        uuid device_id FK
        uuid operation_id UK
        varchar operation_type
        uuid aggregate_id
        varchar status
        jsonb payload_json
        timestamptz client_occurred_at
    }

    ai_conversations {
        uuid id PK
        uuid business_id FK
        uuid store_id FK
        uuid user_id FK
        varchar session_title
        timestamptz created_at
    }

    ai_messages {
        uuid id PK
        uuid business_id FK
        uuid conversation_id FK
        varchar sender_type
        text raw_utterance
        varchar intent_detected
        numeric confidence_score
        jsonb structured_payload
    }

    ai_actions {
        uuid id PK
        uuid business_id FK
        uuid conversation_id FK
        varchar action_type
        jsonb proposed_payload
        varchar status
        uuid executed_entity_id
        uuid confirmed_by_user_id FK
        timestamptz confirmed_at
    }
```
