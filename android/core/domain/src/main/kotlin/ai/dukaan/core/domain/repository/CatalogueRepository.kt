package ai.dukaan.core.domain.repository

import ai.dukaan.core.model.BarcodeLookupResult
import ai.dukaan.core.model.Brand
import ai.dukaan.core.model.Category
import ai.dukaan.core.model.Product
import ai.dukaan.core.model.ProductBarcode
import ai.dukaan.core.model.ProductVariant
import ai.dukaan.core.model.UnitOfMeasure
import kotlinx.coroutines.flow.Flow
import java.math.BigDecimal
import java.util.UUID

data class ProductDraft(
    val name: String,
    val sku: String,
    val categoryId: UUID? = null,
    val brandId: UUID? = null,
    val description: String? = null,
    val imageUrl: String? = null,
    val baseUomId: UUID,
    val sellingPrice: BigDecimal,
    val mrp: BigDecimal,
    val costPrice: BigDecimal = BigDecimal.ZERO,
    val taxRatePercent: BigDecimal = BigDecimal.ZERO,
    val isTaxInclusive: Boolean = true,
    val isLooseItem: Boolean = false,
    val barcodes: List<String> = emptyList(),
    val variants: List<VariantDraft> = emptyList(),
)

data class VariantDraft(
    val variantName: String,
    val sku: String,
    val baseUomId: UUID,
    val costPrice: BigDecimal = BigDecimal.ZERO,
    val sellingPrice: BigDecimal,
    val mrp: BigDecimal,
    val taxRatePercent: BigDecimal = BigDecimal.ZERO,
    val isTaxInclusive: Boolean = true,
    val barcodes: List<String> = emptyList(),
)

data class ProductUpdateDraft(
    val name: String? = null,
    val sku: String? = null,
    val categoryId: UUID? = null,
    val brandId: UUID? = null,
    val description: String? = null,
    val imageUrl: String? = null,
    val baseUomId: UUID? = null,
    val sellingPrice: BigDecimal? = null,
    val mrp: BigDecimal? = null,
    val costPrice: BigDecimal? = null,
    val taxRatePercent: BigDecimal? = null,
    val isTaxInclusive: Boolean? = null,
    val isActive: Boolean? = null,
)

interface CatalogueRepository {
    fun getProducts(
        businessId: UUID,
        query: String? = null,
        categoryId: UUID? = null,
        activeOnly: Boolean = true,
    ): Flow<List<Product>>

    fun getProductById(productId: UUID): Flow<Product?>

    fun findProductByBarcode(businessId: UUID, barcode: String): Flow<BarcodeLookupResult?>

    fun getCategories(businessId: UUID, activeOnly: Boolean = true): Flow<List<Category>>

    fun getBrands(businessId: UUID): Flow<List<Brand>>

    fun getUnitsOfMeasure(): Flow<List<UnitOfMeasure>>

    suspend fun createProduct(businessId: UUID, draft: ProductDraft): Result<Product>

    suspend fun updateProduct(businessId: UUID, productId: UUID, update: ProductUpdateDraft): Result<Product>

    suspend fun deleteProduct(businessId: UUID, productId: UUID): Result<Unit>

    suspend fun createCategory(
        businessId: UUID,
        name: String,
        description: String? = null,
        parentId: UUID? = null,
    ): Result<Category>

    suspend fun createBrand(
        businessId: UUID,
        name: String,
        description: String? = null,
    ): Result<Brand>

    suspend fun registerBarcode(
        businessId: UUID,
        barcode: String,
        productId: UUID,
        variantId: UUID? = null,
        barcodeType: String = "EAN_13",
        isPrimary: Boolean = true,
    ): Result<ProductBarcode>

    suspend fun syncCatalogue(businessId: UUID): Result<Unit>
}
