# DukaanAI: System Architecture

## 1. Architectural System Overview

DukaanAI is designed as an **Offline-First, Distributed Client-Server System** composed of:
1. **Edge Client**: Android application built with Kotlin and Jetpack Compose, operating with an authoritative local Room database.
2. **Cloud Backend**: Python (FastAPI) Modular Monolith providing multi-tenant persistence, sync coordination, and deterministic business rules.
3. **AI Orchestration Plane**: Hybrid NLP engine combining on-device speech/intent preprocessing with cloud LLM entity extraction and conversational querying.

```
+---------------------------------------------------------------------------------+
|                                Android Client                                   |
|                                                                                 |
|  +--------------------+     +---------------------+     +--------------------+  |
|  |   Compose UI       | <-> |  ViewModels & State | <-> | Domain Use Cases   |  |
|  +--------------------+     +---------------------+     +--------------------+  |
|                                                                    |            |
|                             +--------------------------------------+            |
|                             v                                      v            |
|                +-----------------------+              +-----------------------+ |
|                | Room Database (Local) |              | Sync & Network Engine | |
|                +-----------------------+              +-----------------------+ |
+--------------------------------------------------------------------|------------+
                                                                     | HTTPS/TLS 1.3
                                                                     v
+---------------------------------------------------------------------------------+
|                             FastAPI Backend                                     |
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  | Multi-Tenant Gateway & Auth Middleware (tenant_id context extraction)     |  |
|  +---------------------------------------------------------------------------+  |
|         |                                      |                                |
|         v                                      v                                |
|  +-----------------------+            +--------------------------------------+  |
|  | Sync & Ingestion API  |            | Deterministic Ledger & Rules Engine  |  |
|  +-----------------------+            +--------------------------------------+  |
|         |                                      |                                |
|         +-------------------+------------------+                                |
|                             v                                                   |
|             +-------------------------------+                                   |
|             | PostgreSQL (Multi-Tenant DB)  |                                   |
|             +-------------------------------+                                   |
+---------------------------------------------------------------------------------+
                                      |
                                      v
+---------------------------------------------------------------------------------+
|                        AI Inference & LLM Orchestrator                          |
|  - Provider-Agnostic LLM Adapter (Claude, OpenAI, Gemini, Local SLM)            |
|  - Structured JSON Output Schema Validation (Pydantic / Tool-Use)               |
|  - Voice Audio Normalization & Hinglish Phonetic Matcher                        |
+---------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles & Invariants

### 2.1 Principle 1: Offline-First Operation
The Android client must function with full fidelity when offline. Counter sales, credit ledger entries, and inventory adjustments are committed locally to Room first. Sync runs as an asynchronous, background WorkManager process.

### 2.2 Principle 2: Deterministic Business Calculations
Financial math and ledger balances are strictly deterministic:
- Android: `java.math.BigDecimal` with explicit rounding modes (`RoundingMode.HALF_EVEN` / Banker's Rounding).
- Backend: Python `decimal.Decimal`.
- Floating-point representations (`float`, `double`) are strictly prohibited for monetary values and inventory quantities.

### 2.3 Principle 3: Auditable Immutable Stock Ledger
Inventory quantities are never directly updated with an arbitrary `UPDATE products SET stock = X`. Instead:
- Every inventory event is an immutable entry in `StockMovementJournal`.
- Fields: `movement_id (UUID)`, `tenant_id`, `store_id`, `product_id`, `movement_type (PURCHASE, SALE, DAMAGE, RETURN, AUDIT_ADJUSTMENT)`, `quantity_delta`, `unit_cost`, `balance_after`, `created_at`, `idempotency_key`.
- Current stock is guaranteed by ledger aggregation with periodic checkpointing.

### 2.4 Principle 4: Tenant Scoping by Construction
- Every entity has a non-nullable `tenant_id: UUID`.
- Backend utilizes context variables populated by authentication middleware to inject `tenant_id` into all database sessions and queries automatically.
- No cross-tenant data leaks are possible at query level.

---

## 3. Data Sync & Conflict Resolution

### 3.1 Idempotency
All mutating sync requests from the client carry an immutable client-generated `idempotency_key: UUID`. Repeated deliveries due to network timeouts will safely return the original acknowledgement without duplicate execution.

### 3.2 Sync Protocol
- **Outbox Pattern on Client**: Local mutations record an entry in `outbox_events` within the same Room transaction.
- **Server Ingestion**: Server applies events sequentially per tenant in transaction boundaries.
- **Conflict Strategy**:
  - Financial Ledger: Append-only ledger entries never conflict.
  - Catalog / Product Metadata: Last-Write-Wins (LWW) based on NTP-synced UTC timestamp or server-assigned version sequence.
  - Inventory Movements: Absolute movements (`+5`, `-2`) are commuted to the server journal.

---

## 4. Multi-Store Scalability

While DukaanAI starts as single-store per merchant, the data model requires:
- `tenant_id`: Identifies the merchant account / legal entity.
- `store_id`: Identifies the physical branch / outlet.
For single-store setups, `store_id` defaults to the primary default store created during registration.

---

## 5. Security & Privacy

1. **At Rest**: Android Room database encrypted via SQLCipher; backend PostgreSQL encrypted at volume level (AWS KMS).
2. **In Transit**: TLS 1.3 enforced for all network calls with certificate pinning option on mobile.
3. **Voice Audio Privacy**: Audio recordings are processed ephemerally for transcript extraction and discarded immediately unless merchant explicitly opts in for model fine-tuning.
