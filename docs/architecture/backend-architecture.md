# DukaanAI: Backend Architecture

## 1. High-Level Backend Overview

The DukaanAI backend is structured as a **FastAPI Modular Monolith** in Python 3.12. It delivers:
- Multi-tenant data isolation.
- Offline-to-cloud bidirectional synchronization APIs.
- Deterministic double-entry financial ledger and inventory auditing services.
- AI orchestration gateway bridging mobile speech/text input with LLMs.

```
+--------------------------------------------------------------------------------+
|                             API Transport Layer                                |
|  - FastAPI Routers (/api/v1/health, /api/v1/sync, /api/v1/ai)                  |
|  - Request validation via Pydantic v2 schemas                                  |
|  - Dependency injection (get_db, get_current_tenant, get_current_user)         |
+--------------------------------------------------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                          Tenant & Security Middleware                          |
|  - Extracts and validates Bearer JWT & X-Tenant-Id                             |
|  - Sets tenant context variable (contextvars.ContextVar)                       |
|  - Structured request logging (correlation_id, tenant_id, execution_time_ms)   |
+--------------------------------------------------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                              Domain Services Layer                             |
|  - Pure business logic & transactional rules                                   |
|  - StockLedgerService: Appends stock journal movements & computes audits      |
|  - CreditLedgerService: Double-entry customer credit & settlement math         |
|  - SyncOrchestrator: Ingests client outbox batches idempotently                |
+--------------------------------------------------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                           Persistence & Data Layer                             |
|  - SQLAlchemy 2.0 Async Session                                                |
|  - PostgreSQL Database (UUID primary keys, Numeric(15, 4) decimal fields)     |
|  - Tenant-scoped queries enforced via repository filters                       |
|  - Alembic database migration management                                       |
+--------------------------------------------------------------------------------+
```

---

## 2. Directory Layout

```
backend/
├── app/
│   ├── main.py               # FastAPI application factory & lifespan handler
│   ├── core/
│   │   ├── config.py         # Pydantic Settings (ENV loading, defaults)
│   │   ├── logging.py        # Structured JSON logger setup
│   │   ├── security.py       # JWT verification, password hashing (future)
│   │   └── context.py        # Request context variables (tenant_id, request_id)
│   ├── api/
│   │   ├── router.py         # Main API router aggregator
│   │   ├── health.py         # Liveness & readiness probes (/health)
│   │   └── v1/               # Versioned endpoints (future: sync, auth, ledger)
│   ├── schemas/              # Pydantic request/response transfer models
│   ├── models/               # SQLAlchemy ORM declarative models
│   └── services/             # Domain logic & calculation engines
├── migrations/               # Alembic environment and revision scripts
├── tests/                    # Pytest test suite (unit, integration, api)
│   ├── conftest.py           # Shared fixtures, test client, mock sessions
│   └── test_health.py        # Health probe verification
├── Dockerfile                # Production container definition
├── pyproject.toml            # Build & package metadata
└── requirements.txt          # Pinned dependency requirements
```

---

## 3. Mandatory Engineering Invariants

### 3.1 Tenant Scoping
- All persistent tables must define:
  ```python
  tenant_id: Mapped[uuid.UUID] = mapped_column(
      UUID(as_uuid=True), index=True, nullable=False
  )
  ```
- No query may run against tenant-owned models without a `filter_by(tenant_id=...)` clause or global query filter.

### 3.2 Monetary & Numerical Precision
- Never use `float` in backend schemas or database columns.
- Use `decimal.Decimal` in Python.
- Use `Numeric(precision=15, scale=4)` in PostgreSQL to avoid fractional rounding drift across purchases, tax calculations, and currency conversions.

### 3.3 Idempotent Endpoints
- Mutating endpoints (`POST /api/v1/sync/events`) must require an `X-Idempotency-Key: <UUID>` header.
- Duplicated requests are matched against an `idempotency_records` table and replay previous responses.

---

## 4. Configuration & Secrets

- Follow 12-Factor App methodology: All configuration is sourced from environment variables.
- Pydantic Settings (`pydantic-settings`) reads `.env` with strong type validation at application startup.
- Production secrets (DB passwords, LLM API keys) are supplied via environment variables, never committed to git.
