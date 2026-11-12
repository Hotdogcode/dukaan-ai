# Pricing and Tax Compliance

## 1. Indian Retail Price Invariants
Under Indian consumer protection and legal metrology statutes, charging above the Maximum Retail Price (MRP) printed on an item is illegal. DukaanAI enforces this invariant systematically at three separate layers:

1. **Client-side Domain Validation (`CatalogueRepositoryImpl.kt`):**
   ```kotlin
   if (variant.sellingPrice > variant.mrp) {
       throw IllegalArgumentException("Selling price cannot exceed MRP")
   }
   if (variant.sellingPrice < BigDecimal.ZERO || variant.mrp < BigDecimal.ZERO || variant.purchasePrice < BigDecimal.ZERO) {
       throw IllegalArgumentException("Prices cannot be negative")
   }
   ```
2. **Backend Domain Service (`catalogue_service.py`):**
   ```python
   if selling_price > mrp:
       raise BusinessRuleViolation("selling_price cannot exceed mrp")
   ```
3. **Database Constraint (`product_variants` table):**
   ```sql
   CONSTRAINT chk_variant_selling_price_mrp CHECK (selling_price <= mrp),
   CONSTRAINT chk_variant_prices_positive CHECK (
       purchase_price >= 0 AND selling_price >= 0 AND mrp >= 0
   )
   ```

## 2. Tax Configuration & GST
- `tax_rate`: GST slab percentage (`0.00%`, `5.00%`, `12.00%`, `18.00%`, `28.00%`).
- `hsn_code`: 4, 6, or 8-digit HSN code for GST invoice generation.
- **Selling Price Tax Treatment:** In Indian retail (kirana), printed MRP and customer selling price are almost always **inclusive of GST**. DukaanAI stores inclusive selling price directly while recording `tax_rate` for backward calculation on tax invoices.
