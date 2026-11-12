package ai.dukaan.core.database.dao

import ai.dukaan.core.database.entity.BrandEntity
import ai.dukaan.core.database.entity.CatalogueOutboxEntity
import ai.dukaan.core.database.entity.CategoryEntity
import ai.dukaan.core.database.entity.ProductBarcodeEntity
import ai.dukaan.core.database.entity.ProductEntity
import ai.dukaan.core.database.entity.ProductVariantEntity
import ai.dukaan.core.database.entity.UnitOfMeasureEntity
import androidx.room.Dao
import androidx.room.Embedded
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Relation
import androidx.room.Transaction
import androidx.room.Update
import kotlinx.coroutines.flow.Flow
import java.util.UUID

data class ProductWithRelations(
    @Embedded
    val product: ProductEntity,

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

@Dao
interface ProductDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertProduct(product: ProductEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertProducts(products: List<ProductEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertVariants(variants: List<ProductVariantEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBarcodes(barcodes: List<ProductBarcodeEntity>)

    @Update
    suspend fun updateProduct(product: ProductEntity)

    @Query("DELETE FROM products WHERE id = :productId")
    suspend fun deleteProductById(productId: UUID)

    @Transaction
    @Query("SELECT * FROM products WHERE business_id = :businessId AND (:activeOnly = 0 OR is_active = 1) ORDER BY name ASC")
    fun getProducts(businessId: UUID, activeOnly: Boolean): Flow<List<ProductWithRelations>>

    @Transaction
    @Query("""
        SELECT * FROM products 
        WHERE business_id = :businessId 
          AND (:activeOnly = 0 OR is_active = 1)
          AND (:categoryId IS NULL OR category_id = :categoryId)
          AND (:query IS NULL OR name LIKE '%' || :query || '%' OR sku LIKE '%' || :query || '%')
        ORDER BY name ASC
    """)
    fun searchProducts(
        businessId: UUID,
        query: String?,
        categoryId: UUID?,
        activeOnly: Boolean
    ): Flow<List<ProductWithRelations>>

    @Transaction
    @Query("SELECT * FROM products WHERE id = :productId")
    fun getProductById(productId: UUID): Flow<ProductWithRelations?>

    @Transaction
    @Query("SELECT * FROM products WHERE id = :productId")
    suspend fun getProductByIdSync(productId: UUID): ProductWithRelations?

    @Transaction
    @Query("""
        SELECT p.* FROM products p
        INNER JOIN product_barcodes b ON p.id = b.product_id
        WHERE p.business_id = :businessId AND b.barcode = :barcode
        LIMIT 1
    """)
    fun findProductByBarcode(businessId: UUID, barcode: String): Flow<ProductWithRelations?>

    @Query("DELETE FROM product_barcodes WHERE product_id = :productId")
    suspend fun deleteBarcodesForProduct(productId: UUID)

    @Query("DELETE FROM product_variants WHERE product_id = :productId")
    suspend fun deleteVariantsForProduct(productId: UUID)
}

@Dao
interface CategoryDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCategories(categories: List<CategoryEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCategory(category: CategoryEntity)

    @Query("SELECT * FROM categories WHERE business_id = :businessId ORDER BY display_order ASC, name ASC")
    fun getCategories(businessId: UUID): Flow<List<CategoryEntity>>

    @Query("SELECT * FROM categories WHERE business_id = :businessId AND is_active = 1 ORDER BY display_order ASC, name ASC")
    fun getActiveCategories(businessId: UUID): Flow<List<CategoryEntity>>

    @Query("SELECT * FROM categories WHERE id = :categoryId")
    suspend fun getCategoryById(categoryId: UUID): CategoryEntity?
}

@Dao
interface BrandDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBrands(brands: List<BrandEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBrand(brand: BrandEntity)

    @Query("SELECT * FROM brands WHERE business_id = :businessId ORDER BY name ASC")
    fun getBrands(businessId: UUID): Flow<List<BrandEntity>>

    @Query("SELECT * FROM brands WHERE id = :brandId")
    suspend fun getBrandById(brandId: UUID): BrandEntity?
}

@Dao
interface UnitOfMeasureDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUnits(units: List<UnitOfMeasureEntity>)

    @Query("SELECT * FROM units_of_measure ORDER BY category ASC, code ASC")
    fun getAllUnits(): Flow<List<UnitOfMeasureEntity>>

    @Query("SELECT * FROM units_of_measure WHERE id = :id")
    suspend fun getUnitById(id: UUID): UnitOfMeasureEntity?
}

@Dao
interface CatalogueOutboxDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(mutation: CatalogueOutboxEntity)

    @Query("SELECT * FROM catalogue_outbox WHERE business_id = :businessId AND synced_at IS NULL ORDER BY created_at ASC")
    suspend fun getPendingMutations(businessId: UUID): List<CatalogueOutboxEntity>

    @Query("UPDATE catalogue_outbox SET synced_at = :syncedAt WHERE id = :mutationId")
    suspend fun markSynced(mutationId: UUID, syncedAt: java.time.Instant)

    @Query("UPDATE catalogue_outbox SET retry_count = retry_count + 1, error_message = :error WHERE id = :mutationId")
    suspend fun markFailed(mutationId: UUID, error: String)

    @Query("DELETE FROM catalogue_outbox WHERE synced_at IS NOT NULL")
    suspend fun cleanSyncedMutations()
}
