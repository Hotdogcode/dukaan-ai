# DukaanAI: Domain Architecture Overview

## 1. Executive Summary & Purpose

**DukaanAI** is an AI-powered retail business management platform engineered specifically for India's unorganized and semi-organized retail sector — predominantly neighborhood kirana (grocery) stores, general provision shops, FMCG merchants, and small retailers (typically operating with 1 to 5 staff members).

Unlike conventional Western Point-of-Sale (POS) or complex Enterprise Resource Planning (ERP) systems, DukaanAI operates under unique environmental and cultural operational paradigms:
1. **Parchuni & Loose Items**: A large portion of goods (rice, wheat flour, pulses, spices, oils) are sold loose by metric weight/volume rather than fixed barcode packages.
2. **Bahi-Khata (Informal Credit Ledger)**: Trust-based customer credit (*Udhar*) represents 30%–60% of total kirana turnover. Clear tracking of running balances, partial repayments (*Jama*), and automated payment reminders is essential for shop survival.
3. **Intermittent Connectivity & Power Outages**: Operations cannot pause when internet connectivity fluctuates. The domain model must support offline-first operations where counter checkout and credit recording remain fully operational without connectivity.
4. **Natural Multimodal Interaction**: Counter transactions are rapid and chaotic. Shopkeepers require voice-first and conversational interfaces in Hinglish (*Hindi-English code-switching*) without compromising on strict double-entry ledger bookkeeping.

This document establishes the strategic Domain-Driven Design (DDD) model for DukaanAI. It provides pure business concepts, aggregates, value objects, business invariants, and state transitions **independent of database schemas, ORMs, UI frameworks, or network protocols**.

---

## 2. Ubiquitous Language (Kirana & Retail Dictionary)

To eliminate semantic ambiguity between software engineering, retail domain experts, and the AI intelligence layer, the following Ubiquitous Language terms are standardized across the codebase and documentation:

| Domain Term | Vernacular / Industry Term | Formal Business Definition |
|---|---|---|
| **Business (Tenant)** | *Vyapar / Dukan* | The root legal and commercial entity that owns stores, holds master accounts, and configures financial settings. |
| **Store** | *Dukan Ki Branch* | A physical retail location owned by a Business where stock is kept and counter transactions take place. |
| **Counter Sale** | *Parchi / Bill* | A retail transaction at the cash counter where goods are transferred to a customer in exchange for immediate payment, credit, or a split. |
| **Credit Ledger (Khata)** | *Bahi-Khata / Udhar Khata* | The running double-entry accounts receivable ledger tracking money owed by a specific customer to the merchant. |
| **Credit Sale** | *Udhar Bikri* | A sale where payment is deferred, increasing the customer's outstanding balance. |
| **Customer Repayment** | *Jama / Wasooli* | Money paid by a customer against their accumulated credit balance. It reduces accounts receivable without generating additional sales revenue. |
| **Customer Advance** | *Peshgi / Advance Jama* | Money deposited by a customer before purchases are made, creating a credit balance in the customer's favor. |
| **Stock Movement** | *Maal Ki Aawajahi* | An immutable, auditable record of physical inventory increase or decrease with an explicit business reason and quantity delta. |
| **Purchase Order / Bill** | *Maal Ki Khareed* | Inward supply of inventory received from a distributor, wholesaler, or manufacturer with corresponding payment liabilities. |
| **Stock Reconciliation** | *Stock Milana / Ginti* | Periodic physical stock counting to detect discrepancies caused by shrinkage, spoilage, or weighing loss. |
| **Weighing Loss / Spoilage** | *Ghatat / Kharabi* | Natural loss of inventory due to moisture loss, dust, packaging tear, or pest damage inherent in loose agricultural commodities. |
| **Loose SKU** | *Khula Maal* | Commodities purchased in bulk sacks (e.g., 50 kg gunny bag of basmati rice) and sold in fractional retail quantities (e.g., 500 grams, 1.5 kg). |
| **Cash Drawer (Till)** | *Galla* | Physical cash held at the counter for day-to-day transaction settlements and petty expense payouts. |
| **Cost of Goods Sold (COGS)** | *Kareed Lagat* | The acquisition cost of inventory items sold during a specific time period. |
| **Gross Margin** | *Munaafa* | Net sales revenue minus Cost of Goods Sold. |

---

## 3. Core Domain Principles & Constraints

### 3.1 Strict Separation: Deterministic Arithmetic vs. Heuristic AI
- **Principle**: The Artificial Intelligence (LLM/NLP) layer is strictly an **untrusted perceptual input parser**.
- **Constraint**: No financial total, discount, tax bracket, stock quantity, or ledger balance may ever be calculated, updated, or projected by an AI model. The AI parses user intent into a typed command draft; the pure domain model calculates, validates, and commits all arithmetic using deterministic decimal mathematics.

### 3.2 Immutability of Financial & Inventory Journals
- **Principle**: Financial transactions and stock movements are append-only historical ledgers.
- **Constraint**: A completed sale, settled payment, or stock movement is never updated via an in-place `UPDATE` mutation. Corrections, voids, and returns are recorded as explicit compensating journal entries with auditable reason codes.

### 3.3 Movement-Based Inventory Invariant
- **Principle**: Stock quantity is a derived state, not an arbitrary mutable field.
- **Constraint**: Current stock for any product at any store must at all times be mathematically explainable as:
  $$\text{Current Stock} = \sum_{i=1}^{n} \text{MovementQuantity}_i$$

### 3.4 Multi-Tenancy by Construction
- **Principle**: All business entities belong strictly to an isolated Tenant (Business).
- **Constraint**: Aggregate IDs and entity lookups are always scoped by `tenant_id` and, where applicable, `store_id`. Cross-tenant querying is impossible at the domain level.

### 3.5 High Precision Monetary Representation
- **Principle**: Floating-point representations (`float`, `double`) are strictly prohibited in the domain model.
- **Constraint**: All financial representations use an immutable `Money` value object backed by fixed-point decimal arithmetic (minimum 4 decimal places for internal calculations, rounded to 2 decimal places using Banker's Rounding / `HALF_EVEN` for customer-facing display).

---

## 4. Architectural Style & Boundaries

DukaanAI follows **Clean Architecture** and **Domain-Driven Design** packaged as a **Modular Monolith**:
- Domain models and business logic have **zero dependencies** on external frameworks, databases, serialization libraries, or transport layers.
- In Kotlin (Android Client): Implemented as pure Kotlin domain classes, interfaces, and value classes under the `:domain` and `:core:model` modules.
- In Python (FastAPI Backend): Implemented as pure Python domain entities, value objects, and domain services under `backend/app/domain/`.
- Communication between bounded contexts is achieved via **strongly typed commands, query interfaces, and domain events**, avoiding tight coupling between context implementations.
