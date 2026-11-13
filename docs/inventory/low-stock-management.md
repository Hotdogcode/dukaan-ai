# Low-Stock & Reorder Management

## 1. Thresholds
Each product variant stores configurable replenishment limits per store:
- `min_stock_level`: Minimum safety buffer.
- `reorder_quantity`: Recommended purchase quantity.

## 2. Stock Categorization
- **OUT_OF_STOCK**: `current_quantity <= 0`.
- **LOW_STOCK**: `0 < current_quantity <= min_stock_level`.
- **IN_STOCK**: `current_quantity > min_stock_level`.
- **NEGATIVE_STOCK**: `current_quantity < 0`.

## 3. Procurement Integration (Preparation for Stage 09)
The Android UI surfaces quick-filter chips for `Low Stock` and `Out of Stock`, facilitating rapid purchase list preparation.
