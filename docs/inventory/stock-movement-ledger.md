# Stock Movement Ledger (Append-Only)

## 1. Principles
The Stock Movement Ledger (`stock_movements`) is the ultimate single source of truth for all inventory changes.
- **Append-Only**: Rows cannot be updated (`UPDATE`) or deleted (`DELETE`).
- **Correction via Counter-Movement**: Erroneous entries are rectified by issuing compensatory movements with an audit reason.
- **Strict Idempotency**: Every movement requires a unique `idempotency_key` (UUID) to guarantee exactly-once processing during offline sync retries.

## 2. Movement Types
| Movement Type | Direction | Description |
|---|---|---|
| `OPENING_STOCK` | IN (+) | Initial stock on onboarding or system migration |
| `PURCHASE_RECEIPT` | IN (+) | Supplier invoice goods receipt |
| `SALE` | OUT (-) | Counter POS billing checkout |
| `SALE_RETURN` | IN (+) | Customer product return |
| `PURCHASE_RETURN` | OUT (-) | Vendor debit note return |
| `ADJUSTMENT_DAMAGE` | OUT (-) | Spoilage, breakage, rodent damage |
| `ADJUSTMENT_THEFT` | OUT (-) | Shoplifting or employee shrinkage |
| `ADJUSTMENT_FOUND` | IN (+) | Found stock during physical counting |
| `ADJUSTMENT_MANUAL_IN` | IN (+) | Manual positive reconciliation |
| `ADJUSTMENT_MANUAL_OUT` | OUT (-) | Manual negative reconciliation |
| `AUDIT_ADJUSTMENT` | IN / OUT | Discrepancy adjustment from Stock Count Session |
| `TRANSFER_OUT` | OUT (-) | Inter-store transit dispatch |
| `TRANSFER_IN` | IN (+) | Inter-store transit arrival |

## 3. Audit Trails
Each movement captures:
- `quantity_delta`: Signed `DECIMAL(12, 4)` indicating the exact stock change.
- `unit_cost`: Cost of the goods at movement time.
- `balance_after_movement`: The snapshot of stock balance immediately after this movement.
- `reference_type` and `reference_id`: Polymorphic link (e.g. `INVENTORY_COUNT_SESSION`, `POS_SALE`).
- `created_by_user_id`: Authenticated staff user who initiated the event.
