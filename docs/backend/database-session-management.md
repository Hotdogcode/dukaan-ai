# Database Session Management & Unit of Work

## Overview
DukaanAI utilizes SQLAlchemy 2.0 with PostgreSQL as the relational datastore. The persistence layer enforces strict transaction safety, connection hygiene, and deterministic boundary control via the Unit of Work (UoW) design pattern.

## Connection Pool & Engine Configuration
The engine is configured in `backend/app/infrastructure/database/session.py`:
- **Pool Type**: `QueuePool` for connection reuse with pooling parameters:
  - `pool_size`: 10 persistent connections.
  - `max_overflow`: 20 burst connections.
  - `pool_timeout`: 30 seconds.
  - `pool_recycle`: 1800 seconds (30 minutes) to prevent stale socket disconnections.
  - `pool_pre_ping`: True (automatically runs `SELECT 1` to verify connection liveness before checking out from pool).
- **Session Factory**: `sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False)` ensures entities retain their loaded attributes even after transactions commit, avoiding lazy loading errors outside of session scopes.

## Session Lifecycle in FastAPI
In FastAPI dependency injection (`get_db_session`):
```python
def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```
- A database session is leased per HTTP request.
- Automatic cleanup occurs in the `finally` block, guaranteeing no connection leaks back to the pool.
- Sessions do NOT automatically commit in endpoints; business modifications require explicit Unit of Work boundary commits.

## Unit of Work (UoW) Pattern
The Unit of Work pattern (`backend/app/infrastructure/database/unit_of_work.py`) abstracts transaction management away from business domain logic:
```python
class UnitOfWork:
    def __init__(self, session: Session):
        self.session = session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
```
### Key Benefits
1. **Atomic Multi-Aggregate Operations**: Operations spanning multiple aggregates (e.g. creating a business, assigning the owner user, provisioning the default store) commit in a single atomic SQL transaction.
2. **Deterministic Rollback**: Any unhandled exception during business processing triggers an immediate `rollback()`, leaving zero partial or corrupt states.
3. **Repository Aggregation**: Repositories operate on the leased session within the Unit of Work scope without managing transaction lifecycles directly.

## Multi-Store & Tenant RLS Hook
For tenant-scoped transactions:
- The session sets session-level transaction parameters (e.g., `app.current_business_id`) before running tenant queries.
- When the session is closed and returned to the pool, connection state resets cleanly.
