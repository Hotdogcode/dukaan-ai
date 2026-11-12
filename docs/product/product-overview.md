# DukaanAI: Product Overview & Strategy

## 1. Executive Summary

**DukaanAI** is an AI-powered retail operating system tailored specifically for India's 12+ million neighborhood kirana and general retail stores. Traditional POS and ERP software fail in this environment due to complex English-only user interfaces, heavy manual data entry requirements, and dependency on persistent broadband. 

DukaanAI solves this by combining **Hinglish voice-first entry**, **offline-first local resilience**, and **automated khata (credit ledger) and inventory auditing**, while keeping financial calculations deterministic and tamper-proof.

---

## 2. Target Market & Personas

### 2.1 Target User Base
1. **Kirana Stores (Grocery & Provision)**: High transaction volume, frequent credit (udhar) cycles, diverse loose and packaged SKUs.
2. **General Retail & Stationery / Hardware**: Multi-category inventory, variable unit pricing, frequent seasonal and supplier price adjustments.
3. **Small Independent Retailers**: 1–5 staff members; owner delegates counter work but requires strict cash and stock auditing.

### 2.2 Primary Persona: "Ramesh Bhai" (Kirana Store Owner)
- **Age**: 42
- **Device**: Android smartphone (sub-₹15,000 / $180 segment, 4GB RAM, intermittent 4G/5G).
- **Language Preference**: Hindi / Hinglish ("Aata 5kg Ramesh ji ke khate me likh do", "Tata Namak ka stock kitna bacha hai?").
- **Core Frustrations**:
  - Time wasted writing paper bahi-khata (customer credit ledgers).
  - Uncollected customer debts due to lack of timely WhatsApp reminders.
  - Stockouts of fast-moving items without early warning.
  - Cash mismatch at the end of the day.

---

## 3. Core Product Capabilities

| Capability Module | Purpose & Scope |
|---|---|
| **Voice-Based Transaction Entry** | Shopkeeper speaks in natural Hinglish; client/cloud extracts items, units, pricing, and counterparty. Confirmed via 1-tap confirmation card. |
| **Product & Catalog Management** | Barcode scanning, pre-populated Indian FMCG master catalog, loose item management (kg, grams, packets, dozens). |
| **Sales & Billing (Counter POS)** | Rapid offline counter checkout, digital WhatsApp receipt sharing, cash/UPI payment tagging. |
| **Customer Credit Ledger (Khata)** | Complete double-entry customer credit/debit tracking, automated payment reminders via WhatsApp/SMS, payment reconciliation. |
| **Auditable Stock Ledger** | Real-time inventory calculation based on an immutable movement ledger (Purchase, Sale, Waste, Return, Audit Correction). |
| **Supplier & Purchase Management** | Purchase order logging, vendor credit management, cost-price tracking. |
| **Expense Tracking** | Store operational expense capture (electricity, rent, staff salary, tea/refreshments). |
| **Conversational AI Assistant** | Ask natural-language business questions: *"Iss hafte sabse zyada kya bika?"*, *"Kaunse customer ka udhar baaki hai?"* |
| **Deterministic Business Analytics** | Daily gross profit, net margins, dead stock analysis, cash vs digital collection ratios. |

---

## 4. Key Architectural & Product Principles

1. **AI Proposes, Deterministic System Executes**:
   - The AI language model is strictly treated as an **untrusted input parser**.
   - Price calculation, tax, discounts, customer balances, and stock balances are **never calculated by LLMs**.
   - The LLM parses user intention into structured payloads (`DraftTransaction`), which pass through domain validation before commit.
2. **Offline-First Guarantees**:
   - Shop operations cannot stall during network outages. Counter billing, customer balance queries, and stock lookups must function with zero connectivity.
3. **Hinglish As A First-Class Language**:
   - Natural mixing of Hindi and English words common in retail jargon (*udhar*, *jama*, *bhav*, *parchuni*, *stock*, *bill*, *expiry*).
4. **Tenant Isolation & Future Multi-Store Scaling**:
   - Every store's financial data is strictly partitioned by `tenant_id`.
   - Data models are prepared with `store_id` to allow merchants with multiple branches to aggregate reports.

---

## 5. Business Model (Freemium SaaS)

- **Free Tier**: Single-store basic counter billing, digital khata up to 50 active customers, basic PDF reports, offline storage.
- **Premium Tier (Monthly/Annual Subscription)**: Unlimited customers, multi-device sync, automated WhatsApp payment reminder integrations, voice AI quota, advanced dead-stock and margin analytics.
- **Enterprise / Multi-Store**: Multiple branches, centralized warehouse management, staff role permissions.
