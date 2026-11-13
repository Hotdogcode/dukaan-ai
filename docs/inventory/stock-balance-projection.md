# Stock Balance Projection

## 1. Architectural Role
The `stock_balances` table serves as a materialized projection of the current inventory state for rapid point-of-sale lookup, reorder threshold alerts, and mobile synchronization.

## 2. Table Definition
- `business_id` (UUID): Tenant boundary with RLS filter.
- `store_id` (UUID): Physical retail outlet.
- `variant_id` (UUID): Product variant identifier.
- `current_quantity` (DECIMAL 12, 4): On-hand stock in store base UOM.
- `reserved_quantity` (DECIMAL 12, 4): Quantity committed to open orders or pending dispatch.
- `available_quantity` (DECIMAL 12, 4, Computed): `current_quantity - reserved_quantity`.
- `moving_average_cost` (DECIMAL 12, 4): Current weighted average cost per unit.
- `min_stock_level` (DECIMAL 12, 4): Threshold triggering low-stock alert.
- `reorder_quantity` (DECIMAL 12, 4): Recommended procurement order size.
- `last_movement_id` (UUID): Foreign key linking the most recent ledger movement.

## 3. Projection Maintenance
Inside a single database transaction:
1. Lock row with `SELECT FOR UPDATE` or acquire transaction lock on the variant.
2. Insert new `stock_movement`.
3. Compute updated balance: `new_qty = current_qty + movement.quantity_delta`.
4. Update moving average cost if inward movement with defined cost.
5. Upsert `stock_balances`.
