# Product Variant Data & Domain Model

## 1. Variant Model Design
Indian retail items frequently exist in multiple sizes, pack configurations, and flavours. 
DukaanAI supports both:
1. **Simple Products:** Products without explicit multiple sizes (e.g. "Matchbox", "Duster"). The system automatically creates a single default `ProductVariant` behind the scenes with `is_default = true`.
2. **Variant Products:** Products with multiple physical SKUs (e.g. "Tata Salt 1 kg", "Tata Salt Lite 1 kg").

## 2. Relational Schema & Tenant Isolation
```sql
CREATE TABLE product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    variant_name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) NOT NULL,
    barcode VARCHAR(100),
    unit_id UUID REFERENCES units_of_measure(id) ON DELETE RESTRICT,
    purchase_price NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    selling_price NUMERIC(12, 4) NOT NULL,
    mrp NUMERIC(12, 4) NOT NULL,
    tax_rate NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    hsn_code VARCHAR(20),
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_product_variants_business_sku UNIQUE (business_id, sku),
    CONSTRAINT chk_variant_selling_price_mrp CHECK (selling_price <= mrp),
    CONSTRAINT chk_variant_prices_positive CHECK (
        purchase_price >= 0 AND selling_price >= 0 AND mrp >= 0
    )
);
```

## 3. Multiple Barcode Mapping
Variants often have multiple barcodes due to manufacturer packaging redesigns or multipack configurations.
```sql
CREATE TABLE product_barcodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    variant_id UUID NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
    barcode VARCHAR(100) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_product_barcodes_business_barcode UNIQUE (business_id, barcode)
);
```

## 4. Client Domain Representation (Android Room)
On Android, `ProductWithRelations` models the full aggregate:
```kotlin
data class ProductWithRelations(
    @Embedded val product: ProductEntity,
    @Relation(
        parentColumn = "id",
        entityColumn = "product_id"
    )
    val variants: List<ProductVariantEntity> = emptyList(),
    @Relation(
        parentColumn = "id",
        entityColumn = "product_id"
    )
    val barcodes: List<ProductBarcodeEntity> = emptyList(),
)
```
This enables zero-latency local queries and atomic transaction loading in Jetpack Compose UI.
