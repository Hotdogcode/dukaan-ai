package ai.dukaan.feature.catalogue

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.domain.repository.CatalogueRepository
import ai.dukaan.core.model.Category
import ai.dukaan.core.model.Product
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
import kotlinx.coroutines.flow.filterNotNull
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

data class ProductListUiState(
    val searchQuery: String = "",
    val selectedCategoryId: UUID? = null,
    val activeOnly: Boolean = true,
    val isRefreshing: Boolean = false,
    val errorMessage: String? = null,
)

@OptIn(ExperimentalCoroutinesApi::class)
@HiltViewModel
class ProductListViewModel @Inject constructor(
    private val appConfigRepository: AppConfigRepository,
    private val catalogueRepository: CatalogueRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(ProductListUiState())
    val uiState: StateFlow<ProductListUiState> = _uiState.asStateFlow()

    val businessId: StateFlow<UUID?> = appConfigRepository.appConfig
        .map { it.selectedBusinessId }
        .distinctUntilChanged()
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val categories: StateFlow<List<Category>> = businessId
        .flatMapLatest { bId ->
            if (bId == null) flowOf(emptyList())
            else catalogueRepository.getCategories(bId, activeOnly = true)
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val products: StateFlow<List<Product>> = combine(
        businessId.filterNotNull(),
        _uiState.map { it.searchQuery }.distinctUntilChanged(),
        _uiState.map { it.selectedCategoryId }.distinctUntilChanged(),
        _uiState.map { it.activeOnly }.distinctUntilChanged(),
    ) { bId, query, catId, activeOnly ->
        Triple(bId, query, Pair(catId, activeOnly))
    }.flatMapLatest { (bId, query, filters) ->
        catalogueRepository.getProducts(
            businessId = bId,
            query = query.ifBlank { null },
            categoryId = filters.first,
            activeOnly = filters.second,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    init {
        viewModelScope.launch {
            businessId.filterNotNull().collect { bId ->
                syncCatalogue(bId)
            }
        }
    }

    fun onSearchQueryChanged(query: String) {
        _uiState.update { it.copy(searchQuery = query) }
    }

    fun onCategorySelected(categoryId: UUID?) {
        _uiState.update {
            it.copy(selectedCategoryId = if (it.selectedCategoryId == categoryId) null else categoryId)
        }
    }

    fun onToggleActiveFilter() {
        _uiState.update { it.copy(activeOnly = !it.activeOnly) }
    }

    fun refresh() {
        val bId = businessId.value ?: return
        viewModelScope.launch {
            _uiState.update { it.copy(isRefreshing = true, errorMessage = null) }
            val result = catalogueRepository.syncCatalogue(bId)
            _uiState.update {
                it.copy(
                    isRefreshing = false,
                    errorMessage = result.exceptionOrNull()?.message,
                )
            }
        }
    }

    private fun syncCatalogue(bId: UUID) {
        viewModelScope.launch {
            catalogueRepository.syncCatalogue(bId)
        }
    }

    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }
}
