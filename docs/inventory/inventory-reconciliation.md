# Inventory Ledger Reconciliation & Repair

## 1. Motivation
Materialized projections can drift due to process aborts, unexpected database failures, or network partitions during writes. The immutable ledger provides a mathematical guarantee to repair projections.

## 2. Reconciliation Procedure
The backend endpoint `POST /api/v1/businesses/{b_id}/stores/{s_id}/inventory/reconcile` executes:
1. Aggregates all ledger movements per variant:
   $$\text{Calculated Balance} = \sum_{\text{movements}} \text{quantity\_delta}$$
2. Re-derives the Moving Weighted Average Cost by replaying inward lot costs in chronological order.
3. Compares `Calculated Balance` with `stock_balances.current_quantity`.
4. Overwrites drifted projections with recomputed truth and logs an audit reconciliation event.
5. Emits a structured report containing repaired variants, discrepancies, and new totals.
