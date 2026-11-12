# DukaanAI — Store Outlets & Hierarchy Architecture

## 1. Domain Model
A `Business` tenant can operate one or more physical `Store` outlets. Every business must have **exactly one primary outlet** (`is_primary = true`), which acts as the default inventory and sales counter.

---

## 2. Single Primary Outlet Invariant

To guarantee that no business ever has multiple primary stores concurrently, PostgreSQL enforces a **partial unique index**:

```sql
CREATE UNIQUE INDEX uq_store_primary_per_business 
ON stores (business_id) 
WHERE is_primary = true;
```

When an outlet is created or updated with `is_primary = true`, the application service transactional logic demotes any previous primary outlet in the same database transaction:

```python
if data.is_primary:
    db.execute(
        update(Store)
        .where(Store.business_id == business_id, Store.is_primary == True)
        .values(is_primary=False)
    )
```

---

## 3. Store Data Schema

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Unique store identifier |
| `business_id` | UUID (FK) | Owning business tenant |
| `name` | VARCHAR(120) | Store display name (e.g., "Main Market Branch") |
| `code` | VARCHAR(30) | Branch code (e.g., "MAIN", "EXP01") |
| `address_line1` | VARCHAR(255) | Street address |
| `city` | VARCHAR(60) | City (e.g., "Mumbai") |
| `state` | VARCHAR(60) | State (e.g., "Maharashtra") |
| `pincode` | VARCHAR(10) | 6-digit postal pincode |
| `phone_number` | VARCHAR(15) | Optional store contact number |
| `is_primary` | BOOLEAN | Primary counter outlet indicator |
| `timezone` | VARCHAR(50) | Timezone (default: "Asia/Kolkata") |
| `is_active` | BOOLEAN | Operational status |
