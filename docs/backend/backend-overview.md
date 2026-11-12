# DukaanAI — Backend Foundation Overview

## 1. Executive Summary

The DukaanAI backend is engineered as a high-throughput, maintainable **Modular Monolith** adhering to **Clean Architecture** and **Domain-Driven Design (DDD)** principles. Built on Python 3.12, FastAPI, and SQLAlchemy 2.0+, it serves as the cloud synchronization and business logic foundation for Indian kirana and retail stores.

The backend delivers sub-50ms counter API response times, phone-number OTP authentication, cryptographically secure rotating JWT sessions, strict tenant isolation via PostgreSQL Row-Level Security (RLS), and a centralized permission-based authorization model.

---

## 2. Layered Architecture

The repository enforces strict boundaries between layers:

```
┌────────────────────────────────────────────────────────┐
│                      API Layer                         │
│  FastAPI Routers, Pydantic DTOs, HTTP Middleware       │
└──────────────────────────┬─────────────────────────────┘
                           │ (Calls)
┌──────────────────────────▼─────────────────────────────┐
│                  Application Layer                     │
│  Application Services, Use Cases, Transaction Bounds   │
└──────────────────────────┬─────────────────────────────┘
                           │ (Enforces)
┌──────────────────────────▼─────────────────────────────┐
│                    Domain Layer                        │
│  Business Invariants, Role Permissions, Value Objects  │
└──────────────────────────┬─────────────────────────────┘
                           │ (Implements)
┌──────────────────────────▼─────────────────────────────┐
│                Infrastructure Layer                    │
│  SQLAlchemy 2.0 Models, RLS Sessions, OTP Providers    │
└────────────────────────────────────────────────────────┘
```

1. **API Layer (`app/api/`)**: Translates HTTP requests to validated Pydantic models, injects security dependencies, and serializes responses. Contains zero business calculations.
2. **Application Layer (`app/application/`)**: Coordinates application workflows (AuthService, BusinessService), manages transaction commits and rollbacks, and coordinates domain logic with infrastructure.
3. **Domain Layer (`app/domain/`)**: Pure business logic, authorization rules, role definitions, and domain invariants independent of HTTP or database frameworks.
4. **Infrastructure Layer (`app/infrastructure/`)**: Concrete persistence via SQLAlchemy 2.0, database sessions, OTP delivery adapters, and security hashing.

---

## 3. Technology Stack Reference

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Runtime** | Python | 3.12+ | High-performance async/sync application runtime |
| **Web Framework** | FastAPI | >=0.115.0 | Async OpenAPI web framework with Pydantic v2 integration |
| **Data Validation** | Pydantic v2 | >=2.10.0 | Request/response validation and settings management |
| **Configuration** | pydantic-settings | >=2.8.0 | Centralized environment variable parsing and validation |
| **ORM / DDL** | SQLAlchemy | >=2.0.36 | Typed declarative mappings with PostgreSQL dialect |
| **Database Driver**| psycopg (v3) | >=3.2.0 | High-performance C-binary PostgreSQL client |
| **Database Engine**| PostgreSQL | 16+ | ACID transactional persistence with Row-Level Security |
| **Migrations** | Alembic | >=1.14.0 | Schema revision management |
| **Security / JWT** | PyJWT | >=2.10.0 | Cryptographic JWT signing and claim validation |
| **Password Hash** | bcrypt | >=4.2.0 | Salted password hashing |
| **HTTP Client** | HTTPX | >=0.28.0 | Async client for automated integration tests |
| **Test Runner** | pytest | >=8.3.0 | Comprehensive unit, integration, and security test suite |
