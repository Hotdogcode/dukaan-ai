# DukaanAI (दुकान AI)

> AI-Powered Retail Business Assistant for Indian Kirana & Independent General Retailers.

---

## 1. Product Vision

**DukaanAI** is purpose-built for India's retail ecosystem — neighborhood kirana stores, convenience shops, and small retailers (1–5 employees). It bridges the gap between chaotic physical shop counters and modern digital business management using **Hinglish voice interactions**, **offline-first local ledgers**, and **deterministic business calculations**.

### Core Value Pillars
- **Hinglish-First Conversational UI**: Shopkeepers record transactions through voice notes, quick audio commands, or text without rigid form filling.
- **Offline-First Resilience**: Full operational capability even during prolonged connectivity drops or weak 4G/2G network environments.
- **Auditable Financial & Inventory Integrity**: Strict double-entry accounting principles and immutable stock movement journals. AI extracts intent; business logic deterministically executes.
- **Multi-Tenant & Multi-Store Foundation**: Scalable architecture scoped by tenant with support for future multi-outlet retail chains.

---

## 2. Architecture Overview

```
+-------------------------------------------------------------------------+
|                              Android Client                             |
|  - Jetpack Compose + Material 3 UI                                      |
|  - Clean Architecture & MVVM (Hilt, Flow, Coroutines)                   |
|  - Offline-First Storage (Room DB, Encrypted DataStore)                 |
|  - On-Device Audio Capture & Intent Parsing Abstraction                |
+-------------------------------------------------------------------------+
                                    | (HTTPS / Sync Protocol / REST)
                                    v
+-------------------------------------------------------------------------+
|                          Backend Modular Monolith                       |
|  - FastAPI (Python 3.12) Async Architecture                             |
|  - Multi-Tenant Scoping Middleware                                      |
|  - Deterministic Calculation & Ledger Engine                            |
|  - PostgreSQL Database (UUIDs, Decimal precision, Audit logs)           |
+-------------------------------------------------------------------------+
                                    | (AI Orchestration Layer)
                                    v
+-------------------------------------------------------------------------+
|                        Hybrid AI Engine & LLM Layer                     |
|  - Provider-Agnostic LLM Interface (Cloud Inference)                   |
|  - Hinglish Intent Recognition & Slot Extraction Pipeline               |
|  - Strict Separation: AI Proposes -> Deterministic Engine Validates     |
+-------------------------------------------------------------------------+
```

---

## 3. Repository Structure

```
dukaanai/
├── android/                 # Native Android Application
│   ├── app/                 # Application Entry Point & Navigation
│   ├── core/                # Reusable Core Modules (common, designsystem, model)
│   ├── feature/             # Feature Modules (pos, inventory, credit, analytics)
│   ├── domain/              # Pure Kotlin Business Rules & Use Cases
│   ├── ai/                  # Client-side AI Abstraction & Voice Processing
│   └── build-logic/         # Shared Gradle Convention Plugins
├── backend/                 # FastAPI Modular Monolith
│   ├── app/                 # Application Code (api, core, domains)
│   ├── migrations/          # Alembic Database Migrations
│   └── tests/               # Backend Test Suite (pytest, httpx)
├── ml/                      # Machine Learning & NLP Pipelines
│   ├── datasets/            # Hinglish Retail Corpora & Benchmarks
│   ├── preprocessing/       # Audio Normalization & Text Tokenization
│   ├── intent/              # Intent Classification Models
│   ├── extraction/          # Entity & Slot Extraction (NER)
│   └── evaluation/          # Accuracy, Latency & Precision Benchmarks
├── docs/                    # Architectural & Operational Documentation
│   ├── product/             # PRD, Personas & User Journeys
│   ├── architecture/        # System, Android, Backend & AI Architecture
│   ├── database/            # Schemas, Ledger Design & Indexing Strategy
│   ├── api/                 # OpenAPI Specs & Sync Contracts
│   ├── ai/                  # Prompt Specs, Tool Schemas & Guardrails
│   └── development/         # Coding Standards & Development Roadmap
└── infrastructure/          # Deployment & Operations
    ├── docker/              # Dockerfiles & Docker Compose Services
    ├── aws/                 # CloudFormation / Terraform Infrastructure
    └── ci-cd/               # GitHub Actions Workflows & Automation
```

---

## 4. Technology Stack

| Layer | Technologies |
|---|---|
| **Android** | Kotlin 2.0, Jetpack Compose, Material 3, Hilt, Room, Retrofit, Coroutines/Flow, Navigation Compose, WorkManager |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL, Redis (deferred) |
| **AI / NLP** | Provider-independent LLM abstraction, Whisper/Vosk audio ingestion, Hinglish tokenizer & slot-filler |
| **DevOps** | Docker, Docker Compose, AWS-ready deployment, GitHub Actions |

---

## 5. Getting Started

### Prerequisites
- **JDK**: OpenJDK 21
- **Android SDK**: API Level 35 (min API 26)
- **Python**: Python 3.12+
- **Git**: 2.40+

### Backend Local Run
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Health check endpoint: `http://127.0.0.1:8000/health`
Interactive documentation: `http://127.0.0.1:8000/docs`

### Android Local Build
```bash
cd android
./gradlew assembleDebug
```

---

## 6. Architecture Constraints & Invariants

1. **Deterministic Finance**: All math (tax, discount, unit price, ledger balance) is computed by deterministic code using `BigDecimal` (Kotlin) / `Decimal` (Python). Never LLM calculations.
2. **Double-Entry & Auditable Stock**: Stock balance is an aggregate of immutable ledger transactions (`StockMovementJournal`).
3. **Tenant-Scoped Isolation**: Every query and operation must be scoped by `tenant_id` and prepared for future `store_id` multi-store expansion.
4. **Offline First**: The mobile client is fully operational offline and synchronizes via idempotency-keyed delta logs.

---

## 7. Documentation Index

- [Product Overview](file:///c:/Dukan-AI/docs/product/product-overview.md)
- [System Architecture](file:///c:/Dukan-AI/docs/architecture/system-architecture.md)
- [Android Architecture](file:///c:/Dukan-AI/docs/architecture/android-architecture.md)
- [Backend Architecture](file:///c:/Dukan-AI/docs/architecture/backend-architecture.md)
- [AI Architecture](file:///c:/Dukan-AI/docs/architecture/ai-architecture.md)
- [Coding Standards](file:///c:/Dukan-AI/docs/development/coding-standards.md)
- [Development Roadmap](file:///c:/Dukan-AI/docs/development/development-roadmap.md)
