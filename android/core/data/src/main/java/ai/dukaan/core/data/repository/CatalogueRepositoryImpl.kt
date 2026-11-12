package ai.dukaan.core.data.repository

import ai.dukaan.core.database.dao.BrandDao
import ai.dukaan.core.database.dao.CatalogueOutboxDao
import ai.dukaan.core.database.dao.CategoryDao
import ai.dukaan.core.database.dao.ProductDao
import ai.dukaan.core.database.dao.ProductWithRelations
import ai.dukaan.core.database.dao.UnitOfMeasureDao
import ai.dukaan.core.database.entity.BrandEntity
import ai.dukaan.core.database.entity.CatalogueOutboxEntity
import ai.dukaan.core.database.entity.CategoryEntity
import ai.dukaan.core.database.entity.ProductBarcodeEntity
import ai.dukaan.core.database.entity.ProductEntity
import ai.dukaan.core.database.entity.ProductVariantEntity
import ai.dukaan.core.database.entity.UnitOfMeasureEntity
import ai.dukaan.core.domain.repository.CatalogueRepository
import ai.dukaan.core.domain.repository.ProductDraft
import ai.dukaan.core.domain.repository.ProductUpdateDraft
import ai.dukaan.core.model.BarcodeLookupResult
import ai.dukaan.core.model.Brand
import ai.dukaan.core.model.Category
import ai.dukaan.core.model.Product
import ai.dukaan.core.model.ProductBarcode
import ai.dukaan.core.model.ProductVariant
import ai.dukaan.core.model.UnitOfMeasure
import ai.dukaan.core.network.api.CatalogueApiService
import ai.dukaan.core.network.model.BrandCreateNetwork
import ai.dukaan.core.network.model.CategoryCreateNetwork
import ai.dukaan.core.network.model.ProductBarcodeCreateNetwork
import ai.dukaan.core.network.model.ProductCreateNetwork
import ai.dukaan.core.network.model.ProductUpdateNetwork
import ai.dukaan.core.network.model.ProductVariantCreateNetwork
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import java.time.Instant
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CatalogueRepositoryImpl @Inject constructor(
    private val productDao: ProductDao,
    private val categoryDao: CategoryDao,
    private val brandDao: BrandDao,
    private val unitOfMeasureDao: UnitOfMeasureDao,
    private val outboxDao: CatalogueOutboxDao,
    private val apiService: CatalogueApiService,
) : CatalogueRepository {

    override fun getProducts(
        businessId: UUID,
        query: String?,
        categoryId: UUID?,
        activeOnly: Boolean,
    ): Flow<List<Product>> {
        val rawProductsFlow = if (query.isNullOrBlank() && categoryId == null) {
            productDao.getProducts(businessId, activeOnly)
        } else {
            productDao.searchProducts(businessId, query?.trim(), categoryId, activeOnly)
        }

        return combine(
            rawProductsFlow,
            categoryDao.getCategories(businessId),
            brandDao.getBrands(businessId),
            unitOfMeasureDao.getAllUnits(),
        ) { rawProducts, categories, brands, uoms ->
            val catMap = categories.associateBy { it.id }
            val brandMap = brands.associateBy { it.id }
            val uomMap = uoms.associateBy { it.id }

            rawProducts.map { rel ->
                mapToDomainProduct(rel, catMap, brandMap, uomMap)
            }
        }
    }

    override fun getProductById(productId: UUID): Flow<Product?> {
        return productDao.getProductById(productId).map { rel ->
            if (rel == null) null
            else {
                val category = rel.product.categoryId?.let { categoryDao.getCategoryById(it) }
                val brand = rel.product.brandId?.let { brandDao.getBrandById(it) }
                val uom = unitOfMeasureDao.getUnitById(rel.product.baseUomId)
                mapToDomainProduct(
                    rel,
                    category?.let { mapOf(it.id to it) } ?: emptyMap(),
                    brand?.let { mapOf(it.id to it) } ?: emptyMap(),
                    uom?.let { mapOf(it.id to it) } ?: emptyMap(),
                )
            }
        }
    }

    override fun findProductByBarcode(businessId: UUID, barcode: String): Flow<BarcodeLookupResult?> {
        return productDao.findProductByBarcode(businessId, barcode).map { rel ->
            if (rel == null) null
            else {
                val category = rel.product.categoryId?.let { categoryDao.getCategoryById(it) }
                val brand = rel.product.brandId?.let { brandDao.getBrandById(it) }
                val uom = unitOfMeasureDao.getUnitById(rel.product.baseUomId)
                val domainProduct = mapToDomainProduct(
                    rel,
                    category?.let { mapOf(it.id to it) } ?: emptyMap(),
                    brand?.let { mapOf(it.id to it) } ?: emptyMap(),
                    uom?.let { mapOf(it.id to it) } ?: emptyMap(),
                )
                val matchingBarcode = rel.barcodes.find { it.barcode == barcode }
                val matchingVariant = rel.variants.find { it.id == matchingBarcode?.variantId }?.let { v ->
                    ProductVariant(
                        id = v.id,
                        businessId = v.businessId,
                        productId = v.productId,
                        variantName = v.variantName,
                        sku = v.sku,
                        baseUomId = v.baseUomId,
                        purchasePrice = v.purchasePrice,
                        sellingPrice = v.sellingPrice,
                        mrp = v.mrp,
                        taxRatePercent = v.taxRatePercent,
                        isActive = v.isActive,
                    )
                }

                BarcodeLookupResult(
                    barcode = barcode,
                    barcodeType = matchingBarcode?.barcodeType ?: "EAN_13",
                    product = domainProduct,
                    variant = matchingVariant,
                )
            }
        }
    }

    override fun getCategories(businessId: UUID, activeOnly: Boolean): Flow<List<Category>> {
        val flow = if (activeOnly) categoryDao.getActiveCategories(businessId) else categoryDao.getCategories(businessId)
        return flow.map { list ->
            val catMap = list.associateBy { it.id }
            list.map { c ->
                Category(
                    id = c.id,
                    businessId = c.businessId,
                    name = c.name,
                    parentId = c.parentId,
                    parentName = c.parentId?.let { catMap[it]?.name },
                    displayOrder = c.displayOrder,
                    isSystem = c.isSystem,
                    isActive = c.isActive,
                )
            }
        }
    }

    override fun getBrands(businessId: UUID): Flow<List<Brand>> {
        return brandDao.getBrands(businessId).map { list ->
            list.map { b ->
                Brand(
                    id = b.id,
                    businessId = b.businessId,
                    name = b.name,
                    description = b.description,
                    isActive = b.isActive,
                )
            }
        }
    }

    override fun getUnitsOfMeasure(): Flow<List<UnitOfMeasure>> {
        return unitOfMeasureDao.getAllUnits().map { list ->
            list.map { u ->
                UnitOfMeasure(
                    id = u.id,
                    code = u.code,
                    name = u.name,
                    category = u.category,
                    isFractionalAllowed = u.isFractionalAllowed,
                )
            }
        }
    }

    override suspend fun createProduct(businessId: UUID, draft: ProductDraft): Result<Product> = runCatching {
        // Enforce selling_price <= mrp
        if (draft.sellingPrice > draft.mrp) {
            throw IllegalArgumentException("Selling price (${draft.sellingPrice}) cannot exceed MRP (${draft.mrp}).")
        }

        val networkPayload = ProductCreateNetwork(
            name = draft.name,
            sku = draft.sku,
            categoryId = draft.categoryId?.toString(),
            brandId = draft.brandId?.toString(),
            description = draft.description,
            imageUrl = draft.imageUrl,
            baseUomId = draft.baseUomId.toString(),
            sellingPrice = draft.sellingPrice,
            mrp = draft.mrp,
            costPrice = draft.costPrice,
            taxRatePercent = draft.taxRatePercent,
            isTaxInclusive = draft.isTaxInclusive,
            isLooseItem = draft.isLooseItem,
            barcodes = draft.barcodes,
            variants = draft.variants.map { v ->
                ProductVariantCreateNetwork(
                    variantName = v.variantName,
                    sku = v.sku,
                    baseUomId = v.baseUomId.toString(),
                    costPrice = v.costPrice,
                    sellingPrice = v.sellingPrice,
                    mrp = v.mrp,
                    taxRatePercent = v.taxRatePercent,
                    isTaxInclusive = v.isTaxInclusive,
                    barcodes = v.barcodes,
                )
            },
        )

        val response = apiService.createProduct(businessId.toString(), networkPayload)
        if (!response.isSuccessful) {
            val error = response.errorBody()?.string() ?: "Failed with HTTP ${response.code()}"
            throw RuntimeException(error)
        }

        val netProduct = response.body() ?: throw RuntimeException("Empty response body from product creation")
        val productId = UUID.fromString(netProduct.id)

        // Cache in local Room database
        val productEntity = ProductEntity(
            id = productId,
            businessId = businessId,
            name = netProduct.name,
            brandId = netProduct.brandId?.let { UUID.fromString(it) },
            categoryId = netProduct.categoryId?.let { UUID.fromString(it) },
            description = netProduct.description,
            imageUrl = netProduct.imageUrl,
            baseUomId = UUID.fromString(netProduct.baseUomId),
            sku = netProduct.sku,
            purchasePrice = netProduct.costPrice,
            sellingPrice = netProduct.sellingPrice,
            mrp = netProduct.mrp,
            taxRatePercent = netProduct.taxRatePercent,
            hasVariants = netProduct.hasVariants,
            isActive = netProduct.isActive,
            syncStatus = "SYNCED",
        )
        productDao.insertProduct(productEntity)

        // Insert variants & barcodes
        if (netProduct.variants.isNotEmpty()) {
            val variantEntities = netProduct.variants.map { v ->
                ProductVariantEntity(
                    id = UUID.fromString(v.id),
                    businessId = businessId,
                    productId = productId,
                    variantName = v.variantName,
                    sku = v.sku,
                    baseUomId = UUID.fromString(v.baseUomId),
                    purchasePrice = v.costPrice,
                    sellingPrice = v.sellingPrice,
                    mrp = v.mrp,
                    taxRatePercent = v.taxRatePercent,
                    isActive = v.isActive,
                    syncStatus = "SYNCED",
                )
            }
            productDao.insertVariants(variantEntities)
        }

        if (netProduct.barcodes.isNotEmpty()) {
            val barcodeEntities = netProduct.barcodes.map { b ->
                ProductBarcodeEntity(
                    id = UUID.fromString(b.id),
                    businessId = businessId,
                    productId = productId,
                    variantId = b.variantId?.let { UUID.fromString(it) },
                    barcode = b.barcode,
                    barcodeType = b.barcodeType,
                    isPrimary = b.isPrimary,
                )
            }
            productDao.insertBarcodes(barcodeEntities)
        }

        Product(
            id = productId,
            businessId = businessId,
            name = netProduct.name,
            brandId = netProduct.brandId?.let { UUID.fromString(it) },
            brandName = netProduct.brand?.name,
            categoryId = netProduct.categoryId?.let { UUID.fromString(it) },
            categoryName = netProduct.category?.name,
            description = netProduct.description,
            imageUrl = netProduct.imageUrl,
            baseUomId = UUID.fromString(netProduct.baseUomId),
            baseUomCode = netProduct.baseUom?.code,
            sku = netProduct.sku,
            purchasePrice = netProduct.costPrice,
            sellingPrice = netProduct.sellingPrice,
            mrp = netProduct.mrp,
            taxRatePercent = netProduct.taxRatePercent,
            hasVariants = netProduct.hasVariants,
            isActive = netProduct.isActive,
        )
    }

    override suspend fun updateProduct(businessId: UUID, productId: UUID, update: ProductUpdateDraft): Result<Product> = runCatching {
        val payload = ProductUpdateNetwork(
            name = update.name,
            sku = update.sku,
            categoryId = update.categoryId?.toString(),
            brandId = update.brandId?.toString(),
            description = update.description,
            imageUrl = update.imageUrl,
            baseUomId = update.baseUomId?.toString(),
            sellingPrice = update.sellingPrice,
            mrp = update.mrp,
            costPrice = update.costPrice,
            taxRatePercent = update.taxRatePercent,
            isTaxInclusive = update.isTaxInclusive,
            isActive = update.isActive,
        )

        val response = apiService.updateProduct(productId.toString(), businessId.toString(), payload)
        if (!response.isSuccessful) {
            val error = response.errorBody()?.string() ?: "Update failed HTTP ${response.code()}"
            throw RuntimeException(error)
        }

        val netProduct = response.body() ?: throw RuntimeException("Empty response body")
        val productEntity = ProductEntity(
            id = productId,
            businessId = businessId,
            name = netProduct.name,
            brandId = netProduct.brandId?.let { UUID.fromString(it) },
            categoryId = netProduct.categoryId?.let { UUID.fromString(it) },
            description = netProduct.description,
            imageUrl = netProduct.imageUrl,
            baseUomId = UUID.fromString(netProduct.baseUomId),
            sku = netProduct.sku,
            purchasePrice = netProduct.costPrice,
            sellingPrice = netProduct.sellingPrice,
            mrp = netProduct.mrp,
            taxRatePercent = netProduct.taxRatePercent,
            hasVariants = netProduct.hasVariants,
            isActive = netProduct.isActive,
            syncStatus = "SYNCED",
        )
        productDao.updateProduct(productEntity)

        Product(
            id = productId,
            businessId = businessId,
            name = netProduct.name,
            brandId = netProduct.brandId?.let { UUID.fromString(it) },
            brandName = netProduct.brand?.name,
            categoryId = netProduct.categoryId?.let { UUID.fromString(it) },
            categoryName = netProduct.category?.name,
            description = netProduct.description,
            imageUrl = netProduct.imageUrl,
            baseUomId = UUID.fromString(netProduct.baseUomId),
            baseUomCode = netProduct.baseUom?.code,
            sku = netProduct.sku,
            purchasePrice = netProduct.costPrice,
            sellingPrice = netProduct.sellingPrice,
            mrp = netProduct.mrp,
            taxRatePercent = netProduct.taxRatePercent,
            hasVariants = netProduct.hasVariants,
            isActive = netProduct.isActive,
        )
    }

    override suspend fun deleteProduct(businessId: UUID, productId: UUID): Result<Unit> = runCatching {
        val response = apiService.deleteProduct(productId.toString(), businessId.toString())
        if (!response.isSuccessful) {
            val error = response.errorBody()?.string() ?: "Failed to deactivate product HTTP ${response.code()}"
            throw RuntimeException(error)
        }
        val existing = productDao.getProductByIdSync(productId)
        if (existing != null) {
            productDao.updateProduct(existing.product.copy(isActive = false))
        }
    }

    override suspend fun createCategory(
        businessId: UUID,
        name: String,
        description: String?,
        parentId: UUID?,
    ): Result<Category> = runCatching {
        val payload = CategoryCreateNetwork(
            name = name,
            description = description,
            parentId = parentId?.toString(),
        )
        val response = apiService.createCategory(businessId.toString(), payload)
        if (!response.isSuccessful) {
            throw RuntimeException("Failed to create category: ${response.errorBody()?.string()}")
        }
        val net = response.body() ?: throw RuntimeException("Empty response body")
        val catId = UUID.fromString(net.id)
        val entity = CategoryEntity(
            id = catId,
            businessId = businessId,
            name = net.name,
            parentId = net.parentId?.let { UUID.fromString(it) },
            isSystem = net.isSystem,
            isActive = net.isActive,
        )
        categoryDao.insertCategory(entity)
        Category(
            id = catId,
            businessId = businessId,
            name = net.name,
            parentId = net.parentId?.let { UUID.fromString(it) },
            isSystem = net.isSystem,
            isActive = net.isActive,
        )
    }

    override suspend fun createBrand(
        businessId: UUID,
        name: String,
        description: String?,
    ): Result<Brand> = runCatching {
        val payload = BrandCreateNetwork(name = name, description = description)
        val response = apiService.createBrand(businessId.toString(), payload)
        if (!response.isSuccessful) {
            throw RuntimeException("Failed to create brand: ${response.errorBody()?.string()}")
        }
        val net = response.body() ?: throw RuntimeException("Empty response body")
        val brandId = UUID.fromString(net.id)
        val entity = BrandEntity(
            id = brandId,
            businessId = businessId,
            name = net.name,
            description = net.description,
            isActive = net.isActive,
        )
        brandDao.insertBrand(entity)
        Brand(
            id = brandId,
            businessId = businessId,
            name = net.name,
            description = net.description,
            isActive = net.isActive,
        )
    }

    override suspend fun registerBarcode(
        businessId: UUID,
        barcode: String,
        productId: UUID,
        variantId: UUID?,
        barcodeType: String,
        isPrimary: Boolean,
    ): Result<ProductBarcode> = runCatching {
        val payload = ProductBarcodeCreateNetwork(
            barcode = barcode,
            barcodeType = barcodeType,
            isPrimary = isPrimary,
            productId = productId.toString(),
            variantId = variantId?.toString(),
        )
        val response = apiService.registerBarcode(businessId.toString(), payload)
        if (!response.isSuccessful) {
            throw RuntimeException("Failed to register barcode: ${response.errorBody()?.string()}")
        }
        val net = response.body() ?: throw RuntimeException("Empty response body")
        val barcodeId = UUID.fromString(net.id)
        val entity = ProductBarcodeEntity(
            id = barcodeId,
            businessId = businessId,
            productId = productId,
            variantId = variantId,
            barcode = net.barcode,
            barcodeType = net.barcodeType,
            isPrimary = net.isPrimary,
        )
        productDao.insertBarcodes(listOf(entity))
        ProductBarcode(
            id = barcodeId,
            businessId = businessId,
            productId = productId,
            variantId = variantId,
            barcode = net.barcode,
            barcodeType = net.barcodeType,
            isPrimary = net.isPrimary,
        )
    }

    override suspend fun syncCatalogue(businessId: UUID): Result<Unit> = runCatching {
        // 1. Fetch UOMs
        val uomRes = apiService.getUnitsOfMeasure()
        if (uomRes.isSuccessful) {
            val uomList = uomRes.body() ?: emptyList()
            unitOfMeasureDao.insertUnits(uomList.map {
                UnitOfMeasureEntity(
                    id = UUID.fromString(it.id),
                    code = it.code,
                    name = it.name,
                    category = it.category,
                    isFractionalAllowed = it.isFractionalAllowed,
                )
            })
        }

        // 2. Fetch Brands
        val brandRes = apiService.getBrands(businessId.toString(), activeOnly = false)
        if (brandRes.isSuccessful) {
            val brands = brandRes.body() ?: emptyList()
            brandDao.insertBrands(brands.map {
                BrandEntity(
                    id = UUID.fromString(it.id),
                    businessId = businessId,
                    name = it.name,
                    description = it.description,
                    isActive = it.isActive,
                )
            })
        }

        // 3. Fetch Categories
        val catRes = apiService.getCategories(businessId.toString(), activeOnly = false)
        if (catRes.isSuccessful) {
            val categories = catRes.body() ?: emptyList()
            categoryDao.insertCategories(categories.map {
                CategoryEntity(
                    id = UUID.fromString(it.id),
                    businessId = businessId,
                    name = it.name,
                    parentId = it.parentId?.let { p -> UUID.fromString(p) },
                    isSystem = it.isSystem,
                    isActive = it.isActive,
                )
            })
        }

        // 4. Fetch Products (all)
        val prodRes = apiService.listProducts(businessId.toString(), activeOnly = false, pageSize = 200)
        if (prodRes.isSuccessful) {
            val productList = prodRes.body()?.items ?: emptyList()
            val productEntities = mutableListOf<ProductEntity>()
            val variantEntities = mutableListOf<ProductVariantEntity>()
            val barcodeEntities = mutableListOf<ProductBarcodeEntity>()

            for (p in productList) {
                val pId = UUID.fromString(p.id)
                productEntities.add(
                    ProductEntity(
                        id = pId,
                        businessId = businessId,
                        name = p.name,
                        brandId = p.brandId?.let { UUID.fromString(it) },
                        categoryId = p.categoryId?.let { UUID.fromString(it) },
                        description = p.description,
                        imageUrl = p.imageUrl,
                        baseUomId = UUID.fromString(p.baseUomId),
                        sku = p.sku,
                        purchasePrice = p.costPrice,
                        sellingPrice = p.sellingPrice,
                        mrp = p.mrp,
                        taxRatePercent = p.taxRatePercent,
                        hasVariants = p.hasVariants,
                        isActive = p.isActive,
                        syncStatus = "SYNCED",
                    )
                )

                for (v in p.variants) {
                    variantEntities.add(
                        ProductVariantEntity(
                            id = UUID.fromString(v.id),
                            businessId = businessId,
                            productId = pId,
                            variantName = v.variantName,
                            sku = v.sku,
                            baseUomId = UUID.fromString(v.baseUomId),
                            purchasePrice = v.costPrice,
                            sellingPrice = v.sellingPrice,
                            mrp = v.mrp,
                            taxRatePercent = v.taxRatePercent,
                            isActive = v.isActive,
                            syncStatus = "SYNCED",
                        )
                    )
                }

                for (b in p.barcodes) {
                    barcodeEntities.add(
                        ProductBarcodeEntity(
                            id = UUID.fromString(b.id),
                            businessId = businessId,
                            productId = pId,
                            variantId = b.variantId?.let { UUID.fromString(it) },
                            barcode = b.barcode,
                            barcodeType = b.barcodeType,
                            isPrimary = b.isPrimary,
                        )
                    )
                }
            }

            productDao.insertProducts(productEntities)
            if (variantEntities.isNotEmpty()) productDao.insertVariants(variantEntities)
            if (barcodeEntities.isNotEmpty()) productDao.insertBarcodes(barcodeEntities)
        }
    }

    private fun mapToDomainProduct(
        rel: ProductWithRelations,
        categoryMap: Map<UUID, CategoryEntity>,
        brandMap: Map<UUID, BrandEntity>,
        uomMap: Map<UUID, UnitOfMeasureEntity>,
    ): Product {
        val p = rel.product
        val cat = p.categoryId?.let { categoryMap[it] }
        val brand = p.brandId?.let { brandMap[it] }
        val uom = uomMap[p.baseUomId]

        val domainVariants = rel.variants.map { v ->
            val vUom = uomMap[v.baseUomId]
            val vBarcodes = rel.barcodes.filter { it.variantId == v.id }.map { b ->
                ProductBarcode(
                    id = b.id,
                    businessId = b.businessId,
                    productId = b.productId,
                    variantId = b.variantId,
                    barcode = b.barcode,
                    barcodeType = b.barcodeType,
                    isPrimary = b.isPrimary,
                )
            }
            ProductVariant(
                id = v.id,
                businessId = v.businessId,
                productId = v.productId,
                variantName = v.variantName,
                sku = v.sku,
                baseUomId = v.baseUomId,
                baseUomCode = vUom?.code,
                purchasePrice = v.purchasePrice,
                sellingPrice = v.sellingPrice,
                mrp = v.mrp,
                taxRatePercent = v.taxRatePercent,
                isActive = v.isActive,
                barcodes = vBarcodes,
            )
        }

        val domainBarcodes = rel.barcodes.map { b ->
            ProductBarcode(
                id = b.id,
                businessId = b.businessId,
                productId = b.productId,
                variantId = b.variantId,
                barcode = b.barcode,
                barcodeType = b.barcodeType,
                isPrimary = b.isPrimary,
            )
        }

        return Product(
            id = p.id,
            businessId = p.businessId,
            name = p.name,
            brandId = p.brandId,
            brandName = brand?.name,
            categoryId = p.categoryId,
            categoryName = cat?.name,
            description = p.description,
            imageUrl = p.imageUrl,
            baseUomId = p.baseUomId,
            baseUomCode = uom?.code,
            sku = p.sku,
            purchasePrice = p.purchasePrice,
            sellingPrice = p.sellingPrice,
            mrp = p.mrp,
            taxRatePercent = p.taxRatePercent,
            hasVariants = p.hasVariants,
            isActive = p.isActive,
            variants = domainVariants,
            barcodes = domainBarcodes,
            createdAt = p.createdAt,
            updatedAt = p.updatedAt,
        )
    }
}
