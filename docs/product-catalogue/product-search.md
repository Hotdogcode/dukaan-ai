# Product Search Architecture

## 1. Search Requirements for Kirana Operations
Kirana owners need ultra-fast retrieval during billing:
- Prefix matching on product titles (e.g. "mag" -> "Maggi 2-Minute Noodles").
- Brand name matching (e.g. "Amul" -> all Amul dairy and butter items).
- SKU exact matching (e.g. "TATA-SALT-1KG").
- Barcode instant scan-and-find.
- Category filtering with top category pills.

## 2. Server-side Search Implementation
FastAPI endpoint `GET /api/v1/products` executes indexed search:
```python
query_filters = [Product.business_id == business_id]
if not include_inactive:
    query_filters.append(Product.is_active == True)
if category_id:
    query_filters.append(Product.category_id == category_id)
if brand_id:
    query_filters.append(Product.brand_id == brand_id)
if query:
    query_filters.append(
        or_(
            Product.name.ilike(f"%{query}%"),
            Product.sku.ilike(f"%{query}%"),
        )
    )
```

## 3. Client-side Offline Search (Room)
Android Room DAO `ProductDao` executes dynamic SQLite queries reactively via Kotlin Coroutines `Flow`:
```kotlin
@Transaction
@Query("""
    SELECT * FROM products
    WHERE business_id = :businessId
      AND (:categoryId IS NULL OR category_id = :categoryId)
      AND (:activeOnly = 0 OR is_active = 1)
      AND (
          :query IS NULL 
          OR name LIKE '%' || :query || '%' 
          OR sku LIKE '%' || :query || '%'
      )
    ORDER BY name ASC
""")
fun getProductsFlow(
    businessId: UUID,
    query: String?,
    categoryId: UUID?,
    activeOnly: Boolean,
): Flow<List<ProductWithRelations>>
```
Changes to local database instantly stream to Compose UI via `StateFlow` without network dependency.
