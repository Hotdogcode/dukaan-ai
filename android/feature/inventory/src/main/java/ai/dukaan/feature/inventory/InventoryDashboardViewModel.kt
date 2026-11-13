package ai.dukaan.feature.inventory

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.domain.repository.InventoryRepository
import ai.dukaan.core.model.InventorySummary
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
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
import java.math.BigDecimal
import java.util.UUID
import javax.inject.Inject

data class InventoryDashboardUiState(
    val isRefreshing: Boolean = false,
    val errorMessage: String? = null,
    val successMessage: String? = null,
)

@HiltViewModel
class InventoryDashboardViewModel @Inject constructor(
    private val appConfigRepository: AppConfigRepository,
    private val inventoryRepository: InventoryRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(InventoryDashboardUiState())
    val uiState: StateFlow<InventoryDashboardUiState> = _uiState.asStateFlow()

    private val contextFlow = appConfigRepository.appConfig
        .distinctUntilChanged()
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val inventorySummary: StateFlow<InventorySummary?> = contextFlow
        .flatMapLatest { config ->
            val bId = config?.selectedBusinessId
            val sId = config?.selectedStoreId
            if (bId != null && sId != null) {
                inventoryRepository.getInventorySummary(businessId = bId, storeId = sId)
            } else {
                flowOf(null)
            }
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun refresh() {
        val config = contextFlow.value ?: return
        val bId = config.selectedBusinessId ?: return
        val sId = config.selectedStoreId ?: return

        viewModelScope.launch {
            _uiState.update { it.copy(isRefreshing = true, errorMessage = null) }
            inventoryRepository.syncInventory(bId, sId)
            _uiState.update { it.copy(isRefreshing = false) }
        }
    }

    fun reconcile() {
        val config = contextFlow.value ?: return
        val bId = config.selectedBusinessId ?: return
        val sId = config.selectedStoreId ?: return

        viewModelScope.launch {
            _uiState.update { it.copy(isRefreshing = true, errorMessage = null) }
            val res = inventoryRepository.reconcileInventory(bId, sId)
            res.fold(
                onSuccess = { report ->
                    _uiState.update {
                        it.copy(
                            isRefreshing = false,
                            successMessage = "Reconciliation complete: ${report.totalVariantsChecked} checked, ${report.discrepanciesRepaired} repaired.",
                        )
                    }
                },
                onFailure = { err ->
                    _uiState.update { it.copy(isRefreshing = false, errorMessage = err.message ?: "Reconciliation failed") }
                }
            )
        }
    }

    fun clearMessages() {
        _uiState.update { it.copy(errorMessage = null, successMessage = null) }
    }
}
