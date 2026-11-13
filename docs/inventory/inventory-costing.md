# Inventory Costing & Valuation (Weighted Average Cost)

## 1. Costing Model Selection
DukaanAI enforces the **Moving Weighted Average Cost (WAC)** valuation method:
- Kirana stores frequently purchase goods in fluctuating wholesale lots (e.g. sugar, pulses, oil, FMCG).
- Tracking discrete lots with FIFO / LIFO adds immense operational overhead for kirana cashiers.
- WAC smoothly reflects accurate gross margins and balance sheet valuations.

## 2. Mathematical Specification
When an inward movement of goods arrives:
$$\text{New WAC} = \frac{(\text{Current Qty} \times \text{Current WAC}) + (\text{Incoming Qty} \times \text{Incoming Cost})}{\text{Current Qty} + \text{Incoming Qty}}$$

### Edge Cases
1. **Zero Prior Quantity**:
   If `Current Qty <= 0`, `New WAC = Incoming Cost`.
2. **Outward Movements**:
   Outward movements (sales, damage, shrinkage) consume stock at the prevailing `Current WAC` without altering the unit cost.
3. **Total Inventory Valuation**:
   $$\text{Store Inventory Value} = \sum_{v \in \text{Variants}} (\text{current\_quantity}_v \times \text{moving\_average\_cost}_v)$$
4. **Rounding Policy**:
   Calculations are rounded to 4 decimal places using `ROUND_HALF_UP`.
