package ai.dukaan.feature.catalogue

import ai.dukaan.core.domain.repository.CatalogueRepository
import ai.dukaan.core.model.Category
import ai.dukaan.core.model.Product
import ai.dukaan.core.testing.repository.FakeAppConfigRepository
import ai.dukaan.core.testing.rule.MainDispatcherRule
import app.cash.turbine.test
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import java.math.BigDecimal
import java.util.UUID

class ProductListViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private lateinit var appConfigRepository: FakeAppConfigRepository
    private lateinit var catalogueRepository: CatalogueRepository
    private lateinit var viewModel: ProductListViewModel

    private val testBusinessId = UUID.randomUUID()
    private val testCategoryId = UUID.randomUUID()
    private val testUomId = UUID.randomUUID()

    @Before
    fun setUp() {
        appConfigRepository = FakeAppConfigRepository()
        catalogueRepository = mockk(relaxed = true)

        coEvery { catalogueRepository.getCategories(any(), any()) } returns flowOf(
            listOf(
                Category(
                    id = testCategoryId,
                    businessId = testBusinessId,
                    name = "Snacks",
                    parentId = null,
                    parentName = null,
                    displayOrder = 1,
                    isSystem = false,
                    isActive = true,
                )
            )
        )

        coEvery { catalogueRepository.getProducts(any(), any(), any(), any()) } returns flowOf(
            listOf(
                Product(
                    id = UUID.randomUUID(),
                    businessId = testBusinessId,
                    name = "Parle-G 100g",
                    sku = "PARLE-100",
                    categoryId = testCategoryId,
                    baseUomId = testUomId,
                    sellingPrice = BigDecimal("10.00"),
                    mrp = BigDecimal("10.00"),
                    isActive = true,
                )
            )
        )

        coEvery { catalogueRepository.syncCatalogue(any()) } returns Result.success(Unit)

        runBlocking {
            appConfigRepository.setSelectedBusinessId(testBusinessId)
        }
        viewModel = ProductListViewModel(appConfigRepository, catalogueRepository)
    }

    @Test
    fun onSearchQueryChanged_updatesUiStateQuery() = runTest {
        viewModel.onSearchQueryChanged("Parle")
        assertEquals("Parle", viewModel.uiState.value.searchQuery)
    }

    @Test
    fun onCategorySelected_togglesSelection() = runTest {
        viewModel.onCategorySelected(testCategoryId)
        assertEquals(testCategoryId, viewModel.uiState.value.selectedCategoryId)

        // Select again to deselect
        viewModel.onCategorySelected(testCategoryId)
        assertNull(viewModel.uiState.value.selectedCategoryId)
    }

    @Test
    fun onToggleActiveFilter_togglesFlag() = runTest {
        assertTrue(viewModel.uiState.value.activeOnly)
        viewModel.onToggleActiveFilter()
        assertFalse(viewModel.uiState.value.activeOnly)
    }

    @Test
    fun refresh_triggersCatalogueSync() = runTest {
        viewModel.refresh()
        coVerify { catalogueRepository.syncCatalogue(testBusinessId) }
        assertFalse(viewModel.uiState.value.isRefreshing)
        assertNull(viewModel.uiState.value.errorMessage)
    }
}
