# DukaanAI — Production Database Architecture Overview

## 1. Executive Summary

The DukaanAI database architecture transforms the approved Domain-Driven Design (DDD) specifications into an enterprise-grade, multi-tenant relational persistence layer powered by PostgreSQL 16+. Designed for Indian kirana and general retail shops, the persistence model balances extreme write performance on edge POS transactions with ironclad financial determinism, auditable inventory journals, and row-level tenant isolation.

---

## 2. Core Architectural Principles

1. **Strict Relational Integrity**: All entities enforce relational constraints, foreign keys with explicit cascade behaviors (`CASCADE`, `RESTRICT`, `SET NULL`), and database check constraints.
2. **Deterministic Financial Precision**: Under no circumstance is floating-point arithmetic permitted. All currency amounts are stored as `NUMERIC(14, 2)`. Quantities, unit costs, and fractional conversions are stored as `NUMERIC(14, 4)` to support fractional kilograms, milliliters, and moving-average inventory valuation.
3. **PostgreSQL Row-Level Security (RLS)**: Multi-tenancy is enforced natively at the database kernel level across all 39 business-owned tables using RESTRICTIVE RLS policies bound to transaction-local session state (`SET LOCAL app.current_tenant_id`).
4. **Append-Only Accounting & Traceability**: Critical business events—including Stock Movements, Khata Ledger entries, and Cash Movements—are append-only journals. Balances are projections derived from immutable historical movement records.
5. **Idempotent Synchronization**: Edge devices running offline-first Android apps generate client-side UUID idempotency keys. The database enforces uniqueness on `(business_id, idempotency_key)` to guarantee at-most-once processing of queued mutations.
6. **Optimistic Concurrency Control**: High-contention entities like store stock balances utilize integer `version` columns to prevent lost updates during concurrent counter sales or bulk stock receipts.

---

## 3. Database Engine & Connection Strategy

- **Database Engine**: PostgreSQL 16+ (Standard SQL compliance with Native UUIDv4, TIMESTAMPTZ, JSONB, and RLS).
- **Driver**: `psycopg` (v3) binary with asynchronous and synchronous pipeline capabilities.
- **ORM / DDL**: SQLAlchemy 2.0+ typed declarative mappings with Alembic migration versioning.
- **Connection Pooling**:
  - Pool Size: 20 base connections per container instance.
  - Max Overflow: 10 burst connections.
  - Pool Recycle: 1800 seconds (30 minutes) to eliminate stale connections across AWS NLB / PgBouncer.
  - Pool Pre-Ping: Enabled to verify connection liveness prior to transaction checkout.
  - Transaction Scoping: Transaction-level pooling (`PgBouncer` compatible). All RLS context parameters use `SET LOCAL`, guaranteeing that parameters automatically purge upon `COMMIT` or `ROLLBACK`, eliminating pool context leakage.

---

## 4. Context-to-Table Registry (43 Tables)

| Bounded Context | Tables Count | Table Names | Scope |
|---|---|---|---|
| **Identity & Access** | 2 | `users`, `refresh_sessions` | Global / User |
| **Business & Hierarchy** | 3 | `businesses`, `business_users`, `stores` | Multi-Tenant Root |
| **Product Catalogue** | 5 | `categories`, `units_of_measure`, `products`, `product_barcodes`, `unit_conversions` | Catalogue / Tenant |
| **Sales Management** | 5 | `sales`, `sale_items`, `sale_returns`, `sale_return_items`, `sale_reversals` | Store-Scoped |
| **Purchasing & Wholesale** | 5 | `suppliers`, `purchases`, `purchase_items`, `purchase_returns`, `purchase_return_items` | Store-Scoped |
| **Inventory & Movements** | 4 | `stock_movements`, `stock_balances`, `inventory_count_sessions`, `inventory_adjustments` | Store-Scoped Ledger |
| **Customer Credit (Khata)** | 3 | `customers`, `customer_ledger_entries`, `customer_payment_allocations` | Tenant / Store Khata |
| **Supplier Credit (Khata)** | 2 | `supplier_ledger_entries`, `supplier_payment_allocations` | Tenant / Store Khata |
| **Finance & Cash Control** | 5 | `cash_registers`, `expenses`, `payments`, `payment_allocations`, `cash_movements` | Store Financials |
| **Events & Audit** | 3 | `business_events`, `audit_logs`, `idempotency_keys` | Tenant System Audit |
| **Edge Synchronization** | 3 | `device_registrations`, `sync_devices`, `sync_operations` | Sync Hub |
| **AI Assistant (DukaanAI)**| 3 | `ai_conversations`, `ai_messages`, `ai_actions` | Tenant Intelligence |
| **Total** | **43** | | |

---

## 5. Numerical Data Types & Precision Standards

| Domain Concept | PostgreSQL Data Type | Range / Semantics | Example |
|---|---|---|---|
| **Primary Keys** | `UUID` | RFC 4122 v4 UUID | `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` |
| **Foreign Keys** | `UUID` | Strict referential integrity | Reference to parent UUID |
| **Currency Amounts** | `NUMERIC(14, 2)` | Up to ₹999,999,999,999.99 (₹1 Lakh Crore) | `1450.50` |
| **Quantities** | `NUMERIC(14, 4)` | Metric decimal fractions (0.0001 kg = 0.1g) | `1.2500` kg |
| **Unit Cost Basis** | `NUMERIC(14, 4)` | Sub-paisa moving average costs | `42.1875` per kg |
| **Tax Rates** | `NUMERIC(5, 2)` | GST percentage rates (0.00% to 100.00%) | `18.00` % |
| **Timestamps** | `TIMESTAMPTZ` | UTC with explicit timezone offset | `2026-11-12 11:30:00+00` |
| **Metadata / Payloads** | `JSONB` | Binary JSON indexing for sync diffs / AI state | `{"source": "VOICE_COMMAND"}` |
