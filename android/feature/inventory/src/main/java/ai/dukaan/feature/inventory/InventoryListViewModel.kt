package ai.dukaan.feature.inventory

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.domain.repository.InventoryRepository
import ai.dukaan.core.model.InventoryItem
import ai.dukaan.core.model.InventorySummary
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

data class InventoryListUiState(
    val searchQuery: String = "",
    val lowStockOnly: Boolean = false,
    val outOfStockOnly: Boolean = false,
    val isRefreshing: Boolean = false,
    val errorMessage: String? = null,
)

@OptIn(ExperimentalCoroutinesApi::class)
@HiltViewModel
class InventoryListViewModel @Inject constructor(
    private val appConfigRepository: AppConfigRepository,
    private val inventoryRepository: InventoryRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(InventoryListUiState())
    val uiState: StateFlow<InventoryListUiState> = _uiState.asStateFlow()

    private val contextFlow = appConfigRepository.appConfig
        .distinctUntilChanged()
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val inventorySummary: StateFlow<InventorySummary?> = combine(
        contextFlow,
        _uiState,
    ) { config, state ->
        Pair(config, state)
    }
        .flatMapLatest { (config, state) ->
            val bId = config?.selectedBusinessId
            val sId = config?.selectedStoreId
            if (bId != null && sId != null) {
                inventoryRepository.getInventorySummary(
                    businessId = bId,
                    storeId = sId,
                    query = state.searchQuery.ifBlank { null },
                    lowStockOnly = state.lowStockOnly,
                    outOfStockOnly = state.outOfStockOnly,
                )
            } else {
                flowOf(null)
            }
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun onSearchQueryChange(query: String) {
        _uiState.update { it.copy(searchQuery = query) }
    }

    fun onFilterLowStock(enabled: Boolean) {
        _uiState.update { it.copy(lowStockOnly = enabled, outOfStockOnly = if (enabled) false else it.outOfStockOnly) }
    }

    fun onFilterOutOfStock(enabled: Boolean) {
        _uiState.update { it.copy(outOfStockOnly = enabled, lowStockOnly = if (enabled) false else it.lowStockOnly) }
    }

    fun clearFilters() {
        _uiState.update { it.copy(lowStockOnly = false, outOfStockOnly = false, searchQuery = "") }
    }
}
