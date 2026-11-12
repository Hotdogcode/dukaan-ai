# DukaanAI — Multi-Tenant Architecture & PostgreSQL Row-Level Security (RLS)

## 1. Architectural Strategy

DukaanAI employs a **Shared Database, Shared Schema with Row-Level Security (RLS)** architecture. This model provides the optimal balance for SaaS kirana retail:
- **Cost Efficiency**: Hundreds of thousands of small shops share compute, memory, and storage resources without per-tenant database provisioning overhead.
- **Kernel-Level Isolation**: Multi-tenancy is not left solely to application layer `WHERE business_id = ...` queries. The PostgreSQL kernel intercepts every SQL statement (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) and applies restrictive filtering based on session variables.
- **Unified Migrations**: Schema upgrades occur once across the entire cluster, eliminating migration drift across per-tenant schemas or databases.

---

## 2. Row-Level Security Implementation

### A. RLS Policy Specification
All 39 tenant-owned tables have RLS enabled and a `RESTRICTIVE` policy configured:

```sql
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

CREATE POLICY products_tenant_isolation_policy ON products
AS RESTRICTIVE
USING (
    current_setting('app.bypass_rls', true) = 'on'
    OR business_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
)
WITH CHECK (
    current_setting('app.bypass_rls', true) = 'on'
    OR business_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
);
```

### B. Understanding Policy Clauses
1. **`AS RESTRICTIVE`**: Combines with any subsequent permissive policies via logical `AND`. This guarantees that even if a future permissive policy is granted, the tenant boundary can never be breached.
2. **`USING` Clause**: Evaluated on reads (`SELECT`, `UPDATE` target rows, `DELETE` target rows). Prevents unauthorized tenants from observing any data rows belonging to another merchant.
3. **`WITH CHECK` Clause**: Evaluated on writes (`INSERT`, `UPDATE` new rows). Prevents a compromised or buggy client from inserting or updating records into another business's domain.
4. **`NULLIF(..., '')::uuid`**: Safely handles empty string settings, casting valid tenant strings to native UUIDs without crashing on uninitialized settings.

---

## 3. Connection Pooling Safety & Leak Prevention

A critical failure mode in multi-tenant RLS platforms using connection poolers (e.g. `PgBouncer` or SQLAlchemy's `QueuePool`) is **session variable contamination**: if a connection executes `SET app.current_tenant_id = 'tenant-A'`, and the connection is returned to the pool without cleanup, the next request (for tenant-B) might inherit tenant-A's credentials.

### The Solution: Transaction-Scoped `SET LOCAL`
DukaanAI enforces **Transaction-Scoped Session Settings**:

```python
def set_tenant_context(session: Session, tenant_id: uuid.UUID) -> None:
    val = str(uuid.UUID(str(tenant_id)))
    # SET LOCAL scopes the setting strictly to the active transaction.
    session.execute(
        text("SET LOCAL app.current_tenant_id = :tenant_id"), 
        {"tenant_id": val}
    )
```

### Why `SET LOCAL` is Immune to Pool Leakage:
1. `SET LOCAL` applies only to the current transaction.
2. When the transaction completes with `COMMIT` or `ROLLBACK`, PostgreSQL automatically clears the variable back to its default uninitialized state.
3. Even if a worker thread crashes mid-request, the connection rollback cleanses the session state prior to returning the socket to the pool.

---

## 4. Administrative Bypass Mechanism

Certain platform operations must operate across tenant boundaries:
1. **Alembic Migrations**: Schema alterations, index additions, and global data transforms.
2. **Global Analytics Aggregators**: System-wide anonymized retail benchmarks.
3. **Billing & Subscription Reconcilers**: Scheduled jobs updating subscription states across all accounts.

### Controlled Bypass Protocol
Bypass is permitted only within explicitly authenticated background service sessions:

```python
@contextmanager
def admin_bypass_session() -> Generator[Session, None, None]:
    """Admin-only session that enables app.bypass_rls for background maintenance."""
    session = SessionLocal()
    try:
        session.execute(text("SET LOCAL app.bypass_rls = 'on'"))
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

---

## 5. SQLAlchemy 2.0 Integration & Context Manager

Tenant scoping is seamlessly injected into FastAPI request pipelines and background tasks via the `tenant_session` context manager:

```python
from backend.app.infrastructure.database.session import tenant_session

# In Application Service or API Dependency:
with tenant_session(business_id) as session:
    # All queries inside this block are automatically scoped to business_id at the DB engine
    products = session.scalars(select(Product)).all()
    # Attempting to query another tenant's ID returns 0 rows, even with explicit ID:
    # session.get(Product, other_tenant_product_id) -> None
```

---

## 6. Verification and Regression Testing

The tenant isolation architecture is verified automatically in the test suite (`backend/tests/test_database_schema.py`):
1. **Schema Validation**: Asserts that every non-global table (39 tables) contains a non-nullable `business_id` UUID column with an explicit foreign key to `businesses.id`.
2. **Migration Audit**: Asserts that the Alembic migration script defines `ENABLE ROW LEVEL SECURITY` and `CREATE POLICY` on all 39 tenant tables.
3. **Session Behavior**: Asserts that `set_tenant_context` correctly sets `SET LOCAL app.current_tenant_id` with valid UUID validation.
