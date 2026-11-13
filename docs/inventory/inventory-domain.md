# DukaanAI Inventory Domain Architecture

## 1. Overview
The DukaanAI inventory system is engineered specifically for Indian kirana stores and small retail shops. It tracks merchandise at the **Product Variant** level across independent **Stores** within a multi-tenant **Business**.

## 2. Core Domain Principles
1. **Store-Aware Multi-Tenancy**:
   Stock balances are tracked per `(business_id, store_id, variant_id)`. The same variant maintains independent stock balances, reorder points, and costing per physical store location.
2. **Immutable Stock Movement Ledger**:
   Stock quantities are never directly updated without an immutable transaction row in the `stock_movements` ledger.
3. **Current Balance Projection**:
   The `stock_balances` table represents an eventually consistent, high-performance read projection maintained transactionally on each movement.
4. **Moving Weighted Average Cost (WAC)**:
   Inventory valuation strictly uses Moving Weighted Average Cost (WAC). Every inward movement recalculates the unit cost, while outward movements consume stock at the prevailing WAC.
5. **Exact Decimal Precision**:
   Floating-point types (`float`, `double`) are strictly prohibited. All quantities are stored as `DECIMAL(12, 4)` and monetary amounts as `DECIMAL(12, 4)`.

## 3. Key Domain Entities & Relationships
- **Business**: The legal tenant boundary (`tenant_id`).
- **Store**: The physical kirana shop location or warehouse.
- **Product & ProductVariant**: Products hold metadata; variants hold SKUs, barcodes, and units of measure.
- **StockMovement**: The immutable single-source-of-truth ledger event.
- **StockBalance**: Materialized projection of current quantity, reserved quantity, and moving average cost.
- **InventoryCountSession & Items**: Physical stock audit sessions capturing discrepancies and generating adjustment movements.
