# DukaanAI — Inventory Persistence Architecture

## 1. Dual-Table Architecture

Inventory in DukaanAI is modeled around the core principle of **Event-Sourced Accounting**:
1. **The Source of Truth**: An immutable, append-only journal (`stock_movements`).
2. **The Performance Projection**: A fast, cached summary row per store SKU (`stock_balances`).

```mermaid
graph TD
    SM["stock_movements (Immutable Ledger)<br/>- delta (+/-)<br/>- unit_cost<br/>- idempotency_key<br/>- occurred_at"] -->|Aggregates Into| SB["stock_balances (Projection Cache)<br/>- current_quantity<br/>- moving_average_cost<br/>- version (OCC)"]
    
    POS[Counter Sale] -->|Append (-) Movement| SM
    WH[Purchase Receipt] -->|Append (+) Movement| SM
    AUD[Physical Count Audit] -->|Append Adjustment| SM
```

### Why Not Calculate Stock on the Fly?
Calculating current stock via `SUM(quantity_delta) FROM stock_movements WHERE product_id = :p` is accurate but unacceptable for millisecond POS lookups over hundreds of thousands of transactions. The `stock_balances` table acts as a materialized projection cache kept synchronously consistent inside the transaction.

---

## 2. Moving Average Cost (MAC) Valuation

Inventory valuation in DukaanAI strictly uses the **Weighted Moving Average Cost** method.

### The Mathematical Formula:
When new inventory $Q_{\text{new}}$ is received at cost $C_{\text{new}}$ into existing inventory $Q_{\text{current}}$ at current average cost $C_{\text{current}}$:

$$\text{New Cost Basis} = \begin{cases} 
C_{\text{new}} & \text{if } Q_{\text{current}} \le 0 \\
\frac{(Q_{\text{current}} \times C_{\text{current}}) + (Q_{\text{new}} \times C_{\text{new}})}{Q_{\text{current}} + Q_{\text{new}}} & \text{if } Q_{\text{current}} > 0 
\end{cases}$$

### Edge Case: Receiving Stock on Negative Inventory
In real-world Indian kirana stores, goods are frequently unpacked and sold at the counter before the wholesale delivery challan or invoice is entered into the system. As a result, $Q_{\text{current}}$ can legitimately be negative.
- When $Q_{\text{current}} \le 0$, the incoming purchase cost $C_{\text{new}}$ becomes the new moving average cost.
- Sub-paisa fractional precision is guaranteed by storing unit costs as `NUMERIC(14, 4)` and total costs as `NUMERIC(14, 2)`.

---

## 3. Stock Movement Types

Every physical change in inventory is tagged with a domain `movement_type`:

| Movement Type | Delta Sign | Cost Basis Used | Originating Entity |
|---|---|---|---|
| `PURCHASE_RECEIPT` | `+` (Positive) | Supplier Bill Rate | `purchases` / `purchase_items` |
| `SALE_DEDUCTION` | `-` (Negative) | Current Moving Average Cost | `sales` / `sale_items` |
| `SALE_RETURN` | `+` (Positive) | Original Sale Unit Cost Basis | `sale_returns` / `sale_return_items` |
| `PURCHASE_RETURN` | `-` (Negative) | Debit Note Unit Cost | `purchase_returns` / `purchase_return_items` |
| `DAMAGE_SPOILAGE` | `-` (Negative) | Current Moving Average Cost | `inventory_adjustments` |
| `AUDIT_ADJUSTMENT`| `+/-` (Signed) | Current Moving Average Cost | `inventory_adjustments` |

---

## 4. Optimistic Concurrency Control (OCC)

To maintain absolute data integrity without long-lived database locks across distributed mobile terminals, `stock_balances` includes an integer `version` column:

```sql
UPDATE stock_balances
SET current_quantity = current_quantity + :delta,
    moving_average_cost = :new_cost,
    version = version + 1,
    updated_at = now()
WHERE id = :balance_id AND version = :expected_version;
```

If another transaction modified the row concurrently, zero rows are affected. The application service detects this condition and retries the calculation using the newly committed baseline.

---

## 5. Physical Inventory Audits (Stock Counting)

Kirana owners periodically count physical stock on shelves (e.g. at month end or during Diwali inventory checks).

### Count Session Workflow:
1. **Initiate Session**: Cashier or owner opens `inventory_count_sessions` (`status = 'OPEN'`).
2. **Barcode Scanning**: Staff walks aisles scanning barcodes and entering counted physical quantities.
3. **Variance Computation**:
   $$\text{Variance} = \text{Counted Quantity} - \text{System Quantity}$$
4. **Draft Adjustments**: Discrepancies are logged in `inventory_adjustments`.
5. **Manager Approval**:
   - The owner reviews variances.
   - Upon approval, the application service appends compensating `stock_movements` (`movement_type = 'AUDIT_ADJUSTMENT'`) and updates `stock_balances`.
   - The session transitions to `COMPLETED`.
