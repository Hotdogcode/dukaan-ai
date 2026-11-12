package ai.dukaan.core.data

import ai.dukaan.core.data.repository.CatalogueRepositoryImpl
import ai.dukaan.core.database.dao.BrandDao
import ai.dukaan.core.database.dao.CatalogueOutboxDao
import ai.dukaan.core.database.dao.CategoryDao
import ai.dukaan.core.database.dao.ProductDao
import ai.dukaan.core.database.dao.UnitOfMeasureDao
import ai.dukaan.core.database.entity.CategoryEntity
import ai.dukaan.core.domain.repository.ProductDraft
import ai.dukaan.core.network.api.CatalogueApiService
import ai.dukaan.core.network.model.ProductNetwork
import app.cash.turbine.test
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import retrofit2.Response
import java.math.BigDecimal
import java.util.UUID

class CatalogueRepositoryTest {

    private val productDao: ProductDao = mockk(relaxed = true)
    private val categoryDao: CategoryDao = mockk(relaxed = true)
    private val brandDao: BrandDao = mockk(relaxed = true)
    private val unitOfMeasureDao: UnitOfMeasureDao = mockk(relaxed = true)
    private val outboxDao: CatalogueOutboxDao = mockk(relaxed = true)
    private val apiService: CatalogueApiService = mockk(relaxed = true)

    private val repository = CatalogueRepositoryImpl(
        productDao = productDao,
        categoryDao = categoryDao,
        brandDao = brandDao,
        unitOfMeasureDao = unitOfMeasureDao,
        outboxDao = outboxDao,
        apiService = apiService,
    )

    @Test
    fun createProduct_enforcesPriceInvariant_failsWhenSellingPriceExceedsMrp() = runTest {
        val businessId = UUID.randomUUID()
        val draft = ProductDraft(
            name = "Overpriced Parle-G",
            sku = "PG-TEST",
            baseUomId = UUID.randomUUID(),
            sellingPrice = BigDecimal("150.00"),
            mrp = BigDecimal("100.00"), // Invalid: selling price > mrp
        )

        val result = repository.createProduct(businessId, draft)
        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull() is IllegalArgumentException)
        assertTrue(result.exceptionOrNull()?.message?.contains("cannot exceed MRP") == true)
    }

    @Test
    fun createProduct_successfulCreation_savesToRoomAndReturnsProduct() = runTest {
        val businessId = UUID.randomUUID()
        val productId = UUID.randomUUID()
        val uomId = UUID.randomUUID()

        val draft = ProductDraft(
            name = "Parle-G 100g",
            sku = "PG-100G",
            baseUomId = uomId,
            sellingPrice = BigDecimal("10.00"),
            mrp = BigDecimal("10.00"),
            barcodes = listOf("8901234567890"),
        )

        val mockNetworkResponse = ProductNetwork(
            id = productId.toString(),
            businessId = businessId.toString(),
            name = "Parle-G 100g",
            sku = "PG-100G",
            baseUomId = uomId.toString(),
            sellingPrice = BigDecimal("10.00"),
            mrp = BigDecimal("10.00"),
            costPrice = BigDecimal("8.50"),
            taxRatePercent = BigDecimal.ZERO,
            hasVariants = false,
            isActive = true,
        )

        coEvery { apiService.createProduct(businessId.toString(), any()) } returns Response.success(mockNetworkResponse)

        val result = repository.createProduct(businessId, draft)

        assertTrue(result.isSuccess)
        val product = result.getOrNull()
        assertNotNull(product)
        assertEquals(productId, product?.id)
        assertEquals("Parle-G 100g", product?.name)
        assertEquals(BigDecimal("10.00"), product?.sellingPrice)

        // Verify cached in Room ProductDao
        coVerify { productDao.insertProduct(any()) }
    }

    @Test
    fun getCategories_mapsHierarchyCorrectly() = runTest {
        val businessId = UUID.randomUUID()
        val parentId = UUID.randomUUID()
        val childId = UUID.randomUUID()

        val parentCat = CategoryEntity(id = parentId, businessId = businessId, name = "Grocery", displayOrder = 1)
        val childCat = CategoryEntity(id = childId, businessId = businessId, name = "Staples", parentId = parentId, displayOrder = 2)

        coEvery { categoryDao.getActiveCategories(businessId) } returns flowOf(listOf(parentCat, childCat))

        repository.getCategories(businessId, activeOnly = true).test {
            val categories = awaitItem()
            assertEquals(2, categories.size)
            val parent = categories.find { it.id == parentId }
            val child = categories.find { it.id == childId }

            assertEquals("Grocery", parent?.name)
            assertEquals("Staples", child?.name)
            assertEquals("Grocery", child?.parentName)
            awaitComplete()
        }
    }
}
