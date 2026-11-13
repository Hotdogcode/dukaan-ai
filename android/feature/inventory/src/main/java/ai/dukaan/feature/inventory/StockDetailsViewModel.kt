package ai.dukaan.feature.inventory

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.domain.repository.InventoryRepository
import ai.dukaan.core.model.StockMovementRecord
import ai.dukaan.core.model.VariantStockDetails
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

data class StockDetailsUiState(
    val isRefreshing: Boolean = false,
    val errorMessage: String? = null,
)

@OptIn(ExperimentalCoroutinesApi::class)
@HiltViewModel
class StockDetailsViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val appConfigRepository: AppConfigRepository,
    private val inventoryRepository: InventoryRepository,
) : ViewModel() {

    private val variantIdString: String = checkNotNull(savedStateHandle["variantId"])
    val variantId: UUID = UUID.fromString(variantIdString)

    private val _uiState = MutableStateFlow(StockDetailsUiState())
    val uiState: StateFlow<StockDetailsUiState> = _uiState.asStateFlow()

    private val contextFlow = appConfigRepository.appConfig
        .distinctUntilChanged()
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val stockDetails: StateFlow<VariantStockDetails?> = contextFlow
        .flatMapLatest { config ->
            val bId = config?.selectedBusinessId
            val sId = config?.selectedStoreId
            if (bId != null && sId != null) {
                inventoryRepository.getVariantStockDetails(bId, sId, variantId)
            } else {
                flowOf(null)
            }
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    val stockMovements: StateFlow<List<StockMovementRecord>> = contextFlow
        .flatMapLatest { config ->
            val bId = config?.selectedBusinessId
            val sId = config?.selectedStoreId
            if (bId != null && sId != null) {
                inventoryRepository.getStockMovements(bId, sId, variantId)
            } else {
                flowOf(emptyList())
            }
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
}
