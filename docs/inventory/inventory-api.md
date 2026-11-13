# Inventory Management API Reference

Base Path: `/api/v1/businesses/{business_id}/stores/{store_id}/inventory`

### Endpoints
1. `GET /summary`: Paginated catalogue inventory list with overall store valuation and status counts.
2. `GET /low-stock`: Filtered items needing reorder (`current_quantity <= min_stock_level`).
3. `GET /variants/{variant_id}`: Detailed balance, valuation, and threshold metadata.
4. `GET /variants/{variant_id}/movements`: Chronological ledger movement history for the variant.
5. `POST /opening-stock`: Record initial inventory and unit valuation.
6. `POST /adjustments`: Manual stock correction (damage, theft, found, etc.).
7. `POST /counts`: Initialize physical stock audit session.
8. `POST /counts/{session_id}/items`: Log physical count entry for a variant.
9. `POST /counts/{session_id}/complete`: Finalize audit, compute variances, and apply `AUDIT_ADJUSTMENT` movements.
10. `POST /counts/{session_id}/cancel`: Abort audit session without changes.
11. `POST /reconcile`: Rebuild and verify all `stock_balances` from historical `stock_movements`.
