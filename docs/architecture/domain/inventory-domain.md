# DukaanAI: Inventory Domain Deep-Dive & Valuation Strategy

Inventory management is the operational core of a retail store. In Indian kirana stores, inventory tracking presents unique challenges: high transaction velocity, goods sold in loose bulk fractions, price volatility in wholesale procurement, and delays in recording supplier purchase bills.

This document details the movement-based ledger model, operational concurrency, and the inventory valuation architecture.

---

## 1. Movement-Based Ledger Architecture

### 1.1 The Ledger Philosophy
Traditional simple POS systems store inventory as a single mutable column:
$$\text{UPDATE products SET stock = stock - 2;}$$
**This is fundamentally prohibited in DukaanAI.** In-place mutation destroys auditability, makes it impossible to trace inventory shrinkage or fraud, and causes permanent corruption during offline distributed sync.

Instead, DukaanAI models inventory as an **auditable, append-only journal of physical stock movements**:

$$\text{Current Stock} = \sum_{i=1}^{n} \text{MovementQuantity}_i$$

### 1.2 Taxonomy of Stock Movements

Every movement in `StockMovementJournalEntry` is immutable and possesses a strictly typed business reason:

| Movement Type | Algebraic Sign | Triggering Business Context | Reference Entity |
|---|---|---|---|
| `PURCHASE_RECEIPT` | **+ (Positive)** | Inward delivery from wholesale distributor | `PurchaseId` |
| `SALE_DEDUCTION` | **- (Negative)** | Customer purchase at counter checkout | `SaleId` |
| `SALE_RETURN` | **+ (Positive)** | Customer returns unconsumed or defective item | `SaleId` / `ReturnId` |
| `PURCHASE_RETURN` | **- (Negative)** | Damaged goods returned to distributor for debit note | `PurchaseId` / `DebitNoteId` |
| `DAMAGE_SPOILAGE` | **- (Negative)** | Pest damage, bag leakage, moisture loss, expiry | `DamageReportId` |
| `AUDIT_ADJUSTMENT` | **+/- (Variance)**| Physical stock counting reconciliation | `AuditSessionId` |

### 1.3 Journal Entry Structure

```kotlin
data class StockMovementJournalEntry(
    val movementId: StockMovementId,
    val tenantId: BusinessId,
    val storeId: StoreId,
    val productId: ProductId,
    val movementType: StockMovementType,
    val baseQuantityDelta: Decimal,       // Exact signed quantity in BaseUnit (e.g. -2500.0000 grams)
    val unitCostAtMovement: Money?,       // Acquisition cost per base unit at time of movement
    val runningBalanceAfter: Decimal,     // Point-in-time balance snapshot
    val referenceId: UUID,                // SaleId, PurchaseId, or AuditId
    val idempotencyKey: IdempotencyKey,   // Deduplication key
    val occurredAt: Instant,              // Physical business occurrence timestamp
    val recordedAt: Instant               // Ledger entry creation timestamp
)
```

---

## 2. Real-World Operational Realities

### 2.1 Handling Negative Stock (The "Sell First, Bill Later" Reality)
In an ideal enterprise ERP, goods cannot be sold until they are received in the system. In an Indian kirana store, this assumption breaks down daily:
- *Distributor delivery arrives at 8:00 AM during peak morning tea/milk rush.*
- *The delivery boy drops 10 sacks of sugar on the floor, hands a paper challan to the shop assistant, and rushes to the next store.*
- *Customers immediately purchase sugar.*
- *The store owner only enters the formal purchase bill in the evening at 9:00 PM after shop shutters close.*

**Domain Decision**:
1. The inventory engine **does not block sales** when physical stock drops below zero.
2. The stock balance temporarily dips into negative values (e.g., `-5.0000` kg).
3. The UI renders a warning chip (`Negative Stock Alert - Restock Entry Pending`).
4. When the purchase bill is recorded in the evening (+50 kg), the journal naturally evaluates to:
   $$\text{Balance} = -5.0000 + 50.0000 = +45.0000\text{ kg}$$
5. The historical sequence and auditable timeline remain completely intact.

### 2.2 Concurrency & Offline Distributed Sales
When two store staff members (or mobile billing devices) perform counter checkout offline simultaneously:
- Counter 1 sells 2 packets of Parle-G (`Movement: -2`).
- Counter 2 sells 3 packets of Parle-G (`Movement: -3`).
- In an in-place mutation system, Last-Write-Wins (LWW) would overwrite the stock balance, losing one of the sales.
- In DukaanAI's movement-based journal, both movements commute cleanly:
  $$\text{Deduction} = (-2) + (-3) = -5\text{ packets}$$
- Both movements are appended to the ledger without conflict.

---

## 3. Inventory Valuation Strategy: FIFO vs. Weighted Average Cost (WAC)

Accurate inventory valuation is necessary to determine Cost of Goods Sold (COGS) and true Gross Profit margins.

### 3.1 Evaluation of Valuation Methods

#### Option A: First-In, First-Out (FIFO)
- **Mechanism**: Assumes the oldest purchased batches of inventory are sold first. Requires tracking individual purchase lots/batches with separate unit costs.
- **Kirana Reality**:
  - Kirana stores frequently dump new sacks of loose grain into the same open display drums on top of existing grain. Physical separation of lots does not exist.
  - Maintaining lot-by-lot batch picking at a fast-paced retail checkout counter creates unbearable cognitive overhead for shopkeepers.
- **Evaluation**: Complex to maintain for bulk loose commodities; suitable primarily for packaged pharmaceuticals or dated perishable FMCG with strict batch barcodes.

#### Option B: Moving Weighted Average Cost (WAC)
- **Mechanism**: Whenever new inventory is received, the unit cost is recalculated across the combined pooled stock:
  $$\text{New Average Cost} = \frac{(\text{Current Stock} \times \text{Current Average Cost}) + (\text{Received Quantity} \times \text{New Purchase Cost})}{\text{Current Stock} + \text{Received Quantity}}$$
- **Kirana Reality**:
  - Matches physical kirana commodity commingling (loose rice, pulses, sugar, oils).
  - Completely transparent and deterministic.
  - Does not require cashiers to select batches during billing.

---

### 3.2 Formal Architectural Decision

> [!IMPORTANT]
> **DukaanAI adopts Moving Weighted Average Cost (WAC) as the primary inventory valuation strategy for Phase 1.**

### 3.3 Mathematical Specification of Moving Average Cost

When an inward purchase receipt occurs:
$$Q_{\text{prior}} = \text{Current stock balance prior to receipt}$$
$$C_{\text{prior}} = \text{Current moving average cost per base unit}$$
$$Q_{\text{inward}} = \text{Inward quantity received (in base units)}$$
$$C_{\text{inward}} = \text{Purchase unit cost per base unit}$$

If $Q_{\text{prior}} > 0$:
$$C_{\text{new}} = \frac{(Q_{\text{prior}} \times C_{\text{prior}}) + (Q_{\text{inward}} \times C_{\text{inward}})}{Q_{\text{prior}} + Q_{\text{inward}}}$$

If $Q_{\text{prior}} \le 0$ (handling the negative stock scenario):
$$C_{\text{new}} = C_{\text{inward}}$$
*(When stock was previously negative, incoming stock covers the deficit at the newly established purchase cost).*

When an outward sale occurs:
- The item is relieved from inventory at the current $C_{\text{new}}$.
- Cost of Goods Sold (COGS) is recognized as:
  $$\text{COGS} = \text{SoldQuantity} \times C_{\text{new}}$$
- The moving average cost per unit remains unchanged by sales.

### 3.4 Upgrade Path for Packaged Goods with Expiry Dates
For packaged FMCG products carrying manufacturer lot numbers and expiry dates (e.g., baby food, dairy, medicines), the domain model allows an optional `BatchTrackingPolicy` that layers FIFO lot tracking on top of the movement journal without altering the underlying ledger structure.
