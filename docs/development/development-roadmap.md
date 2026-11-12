# DukaanAI: Development Roadmap

## 1. Roadmap Overview & Strategic Phases

DukaanAI is built incrementally using a risk-mitigated, domain-first engineering plan. Each phase delivers a functional, tested increment with clear architectural invariants.

```
+-------------+     +-------------+     +-------------+     +-------------+     +-------------+
|   Phase 0   | --> |   Phase 1   | --> |   Phase 2   | --> |   Phase 3   | --> |   Phase 4   |
| Foundation  |     |  Domain &   |     | Counter POS |     | Customer    |     | Voice AI &  |
|  & Scaffolds|     |  Local DB   |     | & Inventory |     | Credit Khata|     | Conversat.  |
+-------------+     +-------------+     +-------------+     +-------------+     +-------------+
```

---

## 2. Phase Breakdown

### Phase 0: Foundation & Core Scaffolding (Current)
- **Objective**: Establish modular Android project, FastAPI skeleton, documentation, and continuous development environment.
- **Deliverables**:
  - Modular Android Gradle setup with Compose, M3, Hilt, Navigation.
  - FastAPI backend with structured logging, configuration, and health check.
  - Engineering architecture documentation & repository guidelines.
  - Containerization configurations (Dockerfile, docker-compose).
- **Completion Criteria**: Android builds clean; backend tests pass; zero business logic prematurely introduced.

---

### Phase 1: Domain Modeling & Offline Database Engine
- **Objective**: Define pure domain entities, value objects, and authoritative local Room database schemas.
- **Key Modules**:
  - `core/model`: Pure Kotlin data models (`Product`, `StockMovement`, `Customer`, `Transaction`, `Money`).
  - `core/database`: Room entities, TypeConverters (BigDecimal, UUID, Instant), DAOs with transaction support.
  - Deterministic Calculation Engine: Tax, subtotal, and rounding logic with unit tests.
- **Invariants**: 100% test coverage on arithmetic engines; zero Float/Double monetary representations.

---

### Phase 2: Counter POS & Auditable Stock Movement Journal
- **Objective**: Deliver high-speed offline counter checkout and stock tracking.
- **Key Features**:
  - Quick barcode scanner & manual product grid search.
  - Fast receipt generation and counter checkout flow.
  - Immutable `StockMovementJournal` recording purchases, sales, and corrections.
  - Real-time stock alerts for low inventory.

---

### Phase 3: Digital Khata (Customer Credit Ledger)
- **Objective**: Replace physical paper ledgers with an auditable digital credit/debit ledger.
- **Key Features**:
  - Customer profile management with contact information.
  - Credit (*Udhar*) and Settlement (*Jama*) recording with running balance verification.
  - Automated WhatsApp payment reminder message templates with UPI deep-link generation.
  - End-of-day cash and credit reconciliation reports.

---

### Phase 4: Voice-Based Transaction Entry & Hinglish AI
- **Objective**: Enable conversational voice transaction entry for hands-free counter recording.
- **Key Features**:
  - Android audio recording with Voice Activity Detection (VAD).
  - FastAPI speech-to-intent pipeline with Hinglish phonetic normalizer.
  - Provider-agnostic LLM slot extraction into validated Pydantic draft models.
  - 1-tap confirmation card UI on Android client.

---

### Phase 5: Cloud Synchronization & Multi-Tenant Authentication
- **Objective**: Bidirectional synchronization between offline client and cloud database.
- **Key Features**:
  - Merchant phone OTP authentication and JWT issuance.
  - Idempotent outbox sync engine on Android via WorkManager.
  - PostgreSQL database schema with Alembic migrations and tenant-scoped security.
  - Cloud backup and multi-device synchronization.

---

### Phase 6: Multi-Store Retail & Advanced Analytics
- **Objective**: Support merchants expanding to multiple branches.
- **Key Features**:
  - Multi-store hierarchy (`store_id` under `tenant_id`).
  - Inter-store stock transfers.
  - Gross margin, dead stock, and supplier performance analytics.
  - Role-based staff access permissions (Cashier vs Store Manager vs Owner).
