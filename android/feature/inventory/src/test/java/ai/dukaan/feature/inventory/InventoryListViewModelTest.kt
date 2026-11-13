package ai.dukaan.feature.inventory

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.domain.repository.InventoryRepository
import ai.dukaan.core.model.AppConfig
import ai.dukaan.core.model.InventorySummary
import ai.dukaan.core.testing.rule.MainDispatcherRule
import app.cash.turbine.test
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.flow.flowOf
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

class InventoryListViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private val appConfigRepository: AppConfigRepository = mockk(relaxed = true)
    private val inventoryRepository: InventoryRepository = mockk(relaxed = true)

    private val businessId = UUID.randomUUID()
    private val storeId = UUID.randomUUID()

    @Before
    fun setUp() {
        val appConfig = AppConfig(
            selectedBusinessId = businessId,
            selectedStoreId = storeId,
            selectedStoreName = "Main Store",
        )
        every { appConfigRepository.appConfig } returns flowOf(appConfig)
    }

    @Test
    fun initialState_hasEmptyFilters() {
        val viewModel = InventoryListViewModel(appConfigRepository, inventoryRepository)
        val state = viewModel.uiState.value

        assertEquals("", state.searchQuery)
        assertFalse(state.lowStockOnly)
        assertFalse(state.outOfStockOnly)
        assertFalse(state.isRefreshing)
        assertNull(state.errorMessage)
    }

    @Test
    fun onSearchQueryChange_updatesUiState() {
        val viewModel = InventoryListViewModel(appConfigRepository, inventoryRepository)

        viewModel.onSearchQueryChange("Atta")
        assertEquals("Atta", viewModel.uiState.value.searchQuery)

        viewModel.onSearchQueryChange("")
        assertEquals("", viewModel.uiState.value.searchQuery)
    }

    @Test
    fun onFilterLowStock_togglesMutuallyExclusiveWithOutOfStock() {
        val viewModel = InventoryListViewModel(appConfigRepository, inventoryRepository)

        viewModel.onFilterOutOfStock(true)
        assertTrue(viewModel.uiState.value.outOfStockOnly)
        assertFalse(viewModel.uiState.value.lowStockOnly)

        viewModel.onFilterLowStock(true)
        assertTrue(viewModel.uiState.value.lowStockOnly)
        assertFalse(viewModel.uiState.value.outOfStockOnly)
    }

    @Test
    fun clearFilters_resetsQueryAndStatusFilters() {
        val viewModel = InventoryListViewModel(appConfigRepository, inventoryRepository)

        viewModel.onSearchQueryChange("Maggie")
        viewModel.onFilterLowStock(true)
        viewModel.clearFilters()

        assertEquals("", viewModel.uiState.value.searchQuery)
        assertFalse(viewModel.uiState.value.lowStockOnly)
        assertFalse(viewModel.uiState.value.outOfStockOnly)
    }

    @Test
    fun inventorySummary_emitsSummaryWhenConfigured() = runTest {
        val summaryMock = InventorySummary(
            totalItems = 25,
            totalValuation = BigDecimal("45000.00"),
            lowStockCount = 3,
            outOfStockCount = 2,
            items = emptyList(),
            page = 1,
            limit = 50,
            totalPages = 1,
        )

        every {
            inventoryRepository.getInventorySummary(businessId, storeId, any(), any(), any(), any(), any(), any())
        } returns flowOf(summaryMock)

        val viewModel = InventoryListViewModel(appConfigRepository, inventoryRepository)

        viewModel.inventorySummary.test {
            val item = awaitItem()
            // Could be initial null or emitted item depending on collection
            if (item == null) {
                val emitted = awaitItem()
                assertEquals(25, emitted?.totalItems)
                assertEquals(BigDecimal("45000.00"), emitted?.totalValuation)
            } else {
                assertEquals(25, item.totalItems)
                assertEquals(BigDecimal("45000.00"), item.totalValuation)
            }
        }
    }
}
