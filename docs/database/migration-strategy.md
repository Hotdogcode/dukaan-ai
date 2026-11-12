# DukaanAI — Schema Migration Strategy & Alembic Operations

## 1. Schema Evolution Principles

In a retail platform handling active billing at checkout counters, database downtime directly translates to stalled customer lines and lost merchant revenue. Schema evolution in DukaanAI adheres to these strict rules:

1. **Version Controlled DDL**: Every database change—table creations, column additions, indexes, RLS policies, and constraints—must be written in Alembic migration scripts committed to Git.
2. **Backward-Compatible Expansions**: Schema changes must always remain compatible with the currently running application code (Expand-Contract Pattern).
3. **No Raw Manual DDL**: Direct manual execution of `ALTER TABLE` or `CREATE INDEX` on production databases without a corresponding Alembic migration is strictly prohibited.
4. **Mandatory Downgrade Path**: Every `upgrade()` function in Alembic must have a fully implemented, symmetric `downgrade()` function that cleanly reverses all changes.
5. **Dry-Run SQL Review**: Before applying any migration to staging or production, the migration must be generated as raw SQL via `alembic upgrade <rev> --sql` and reviewed for lock contention and table rewrites.

---

## 2. Directory Layout & Configuration

```
backend/
├── alembic.ini                  # Alembic CLI configuration
├── migrations/
│   ├── env.py                   # Environment runner with dynamic settings & RLS support
│   ├── script.py.mako           # Migration script template
│   └── versions/
│       └── 20261112_001_initial_database_schema.py   # Initial production schema
```

### Alembic `env.py` Configuration Highlights:
- Reads database URL directly from `app.core.config.get_settings().DATABASE_URL`.
- Imports `Base.metadata` from `app.infrastructure.database.base` ensuring complete autogenerate detection.
- Supports both **Offline Mode** (`--sql`) for CI dry-run validation and **Online Mode** for container startup.

---

## 3. Operational Command Reference

### Generate Migration from Model Changes:
```bash
# Inside backend directory
alembic revision --autogenerate -m "add_hsn_sac_tax_code_to_products"
```

### Dry-Run SQL Compilation (Offline Mode):
```bash
# Generates complete SQL DDL without touching a live database
alembic upgrade head --sql
```

### Apply Pending Migrations (Online Mode):
```bash
# Applies all pending revisions up to latest head
alembic upgrade head
```

### Check Migration History & Current Version:
```bash
# Display current database version
alembic current

# Display revision history
alembic history --verbose
```

### Rollback Migration:
```bash
# Rollback the most recent migration step
alembic downgrade -1

# Rollback to a specific revision ID
alembic downgrade 001_initial_schema
```

---

## 4. Zero-Downtime Migration Patterns

### A. Adding a New Column
- **Dangerous**: `ALTER TABLE products ADD COLUMN brand_name VARCHAR(100) NOT NULL;` (Requires full table rewrite and blocks all reads/writes while scanning existing rows).
- **Safe Zero-Downtime Pattern**:
  1. Add column as nullable:
     ```sql
     ALTER TABLE products ADD COLUMN brand_name VARCHAR(100) NULL;
     ```
  2. Deploy application code that populates `brand_name` for new writes and handles `null` gracefully.
  3. Backfill existing records in small batches via background worker.
  4. Once backfilled, add `NOT NULL` constraint using `CHECK (brand_name IS NOT NULL) NOT VALID`, then validate asynchronously.

### B. Adding an Index on a High-Volume Table
- **Dangerous**: `CREATE INDEX ix_sales_date ON sales (occurred_at);` (Locks table against writes during index build).
- **Safe Zero-Downtime Pattern**:
  Use PostgreSQL's `CONCURRENTLY` feature:
  ```python
  def upgrade() -> None:
      op.execute(
          "CREATE INDEX CONCURRENTLY ix_sales_date ON sales (occurred_at);"
      )

  def downgrade() -> None:
      op.execute(
          "DROP INDEX CONCURRENTLY IF EXISTS ix_sales_date;"
      )
  ```
  *(Note: Requires setting `autocommit_block()` in Alembic as `CONCURRENTLY` cannot run inside an explicit transaction block).*

### C. Renaming a Column
Direct renaming (`ALTER TABLE ... RENAME COLUMN`) immediately breaks running application containers. Use the **Expand-Contract Phase**:
1. **Phase 1 (Expand)**: Add the new column alongside the old column. Deploy code that writes to both columns and reads from old.
2. **Phase 2 (Backfill)**: Copy historical data from old column to new column.
3. **Phase 3 (Switch)**: Deploy code that reads from new column and writes to new column.
4. **Phase 4 (Contract)**: Drop old column in a subsequent migration.

---

## 5. Automated CI/CD Migration Pipeline

In GitHub Actions (`infrastructure/ci-cd/`):
1. **Pull Request Stage**:
   - Executes `alembic upgrade head --sql`.
   - Runs `pytest tests/test_database_schema.py` to assert that all models match Alembic metadata and constraints.
2. **Deployment Stage**:
   - Runs as a Kubernetes / AWS ECS Pre-Sync Job before rolling out updated application pods:
     ```bash
     alembic upgrade head
     ```
   - If the migration job fails, rollout terminates immediately, preventing new application code from launching against an outdated schema.
