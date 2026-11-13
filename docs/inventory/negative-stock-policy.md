# Negative Stock Policy & Enforcement

## 1. Problem Statement
In fast-paced Indian retail, goods are often sold at the billing counter before the inbound vendor purchase invoice has been entered into the system. Strict disallowance of negative inventory would halt counter sales, creating customer frustration.

## 2. Business-Level Configurable Policy
DukaanAI supports configurable policies via `businesses.negative_stock_policy`:
- `ALLOW_NEGATIVE_STOCK` (Default for small Kiranas): Outward stock movements proceed even when `current_quantity < requested_quantity`. Current quantity becomes negative.
- `DISALLOW_NEGATIVE_STOCK`: Outward stock movements fail immediately with `422 Unprocessable Entity` (`INSUFFICIENT_STOCK`).

## 3. Costing & Projection Handling
- Inward goods receipts when stock is negative immediately offset the negative balance.
- Inventory dashboard displays warning chips and counts for variants operating in negative stock.
- Physical audit counts and reconciliations flag negative balances for staff investigation.
