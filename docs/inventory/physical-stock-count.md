# Physical Stock Count & Audit Sessions

## 1. Lifecycle
Physical stock counting enables periodic auditing of shelf inventory without halting business:
1. **Creation (`IN_PROGRESS`)**: Staff creates an audit session. A unique human-readable session number is assigned (e.g. `COUNT-20261113-1a2b3c4d`).
2. **Item Scanning & Entry**: As items are counted, rows are created in `inventory_count_items`. The system snapshots `system_quantity` at count time and computes `variance_quantity = counted_quantity - system_quantity`.
3. **Completion (`COMPLETED`)**: When the audit is finalized:
   - For every variant with non-zero variance, an `AUDIT_ADJUSTMENT` movement is generated in `stock_movements`.
   - `stock_balances` are updated to match physical reality.
   - Financial variance valuation is calculated: `variance_value = variance_quantity * unit_cost`.
4. **Cancellation (`CANCELLED`)**: An unfinalized audit can be aborted without any balance adjustments.
