# Opening Stock Entry Workflow

## 1. Overview
When a retailer migrates to DukaanAI or introduces a new variant to a store, opening stock must be recorded to establish initial physical inventory and baseline unit valuation.

## 2. Invariants & Business Rules
- Quantity must be strictly positive (`> 0`).
- Unit cost must be non-negative (`>= 0`).
- Single-entry guarantee per variant per store: Attempting to record opening stock on a variant that already possesses an `OPENING_STOCK` movement is rejected with `409 Conflict`. Subsequent modifications must be processed via Stock Adjustments.
- An `OPENING_STOCK` movement row is inserted into `stock_movements`.
- The `stock_balances` record is created or updated with the initial quantity and moving average cost.
