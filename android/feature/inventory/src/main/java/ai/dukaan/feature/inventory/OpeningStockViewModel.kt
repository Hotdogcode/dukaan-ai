package ai.dukaan.feature.inventory

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.domain.repository.InventoryRepository
import ai.dukaan.core.model.InventoryItem
import ai.dukaan.core.model.OpeningStockRequestModel
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
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.math.BigDecimal
import java.util.UUID
import javax.inject.Inject

data class OpeningStockUiState(
    val selectedVariantId: UUID? = null,
    val selectedVariantName: String = "",
    val quantityText: String = "",
    val unitCostText: String = "",
    val notesText: String = "",
    val isSubmitting: Boolean = false,
    val errorMessage: String? = null,
    val isSuccess: Boolean = false,
) {
    val quantity: BigDecimal?
        get() = quantityText.toBigDecimalOrNull()

    val unitCost: BigDecimal?
        get() = unitCostText.toBigDecimalOrNull()

    val isValid: Boolean
        get() = selectedVariantId != null &&
                (quantity ?: BigDecimal.ZERO) > BigDecimal.ZERO &&
                (unitCost ?: BigDecimal.ZERO) >= BigDecimal.ZERO
}

@OptIn(ExperimentalCoroutinesApi::class)
@HiltViewModel
class OpeningStockViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val appConfigRepository: AppConfigRepository,
    private val inventoryRepository: InventoryRepository,
) : ViewModel() {

    private val initialVariantId: String? = savedStateHandle["variantId"]

    private val _uiState = MutableStateFlow(OpeningStockUiState())
    val uiState: StateFlow<OpeningStockUiState> = _uiState.asStateFlow()

    private val contextFlow = appConfigRepository.appConfig
        .distinctUntilChanged()
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val variants: StateFlow<List<InventoryItem>> = contextFlow
        .flatMapLatest { config ->
            val bId = config?.selectedBusinessId
            val sId = config?.selectedStoreId
            if (bId != null && sId != null) {
                inventoryRepository.getInventorySummary(bId, sId, limit = 200)
            } else {
                flowOf(null)
            }
        }
        .flatMapLatest { summary -> flowOf(summary?.items ?: emptyList()) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    init {
        initialVariantId?.let { idStr ->
            runCatching { UUID.fromString(idStr) }.getOrNull()?.let { vId ->
                onSelectVariant(vId, "Selected Variant")
            }
        }
    }

    fun onSelectVariant(variantId: UUID, name: String) {
        _uiState.update {
            it.copy(
                selectedVariantId = variantId,
                selectedVariantName = name,
            )
        }
    }

    fun onQuantityChange(text: String) {
        _uiState.update { it.copy(quantityText = text) }
    }

    fun onUnitCostChange(text: String) {
        _uiState.update { it.copy(unitCostText = text) }
    }

    fun onNotesChange(text: String) {
        _uiState.update { it.copy(notesText = text) }
    }

    fun submit() {
        val s = _uiState.value
        val config = contextFlow.value ?: return
        val bId = config.selectedBusinessId ?: return
        val sId = config.selectedStoreId ?: return
        val vId = s.selectedVariantId ?: return
        val qty = s.quantity ?: return
        val cost = s.unitCost ?: return

        viewModelScope.launch {
            _uiState.update { it.copy(isSubmitting = true, errorMessage = null) }
            val req = OpeningStockRequestModel(
                variantId = vId,
                quantity = qty,
                unitCost = cost,
                notes = s.notesText.trim().ifBlank { null },
            )
            val res = inventoryRepository.recordOpeningStock(bId, sId, req)
            res.fold(
                onSuccess = {
                    _uiState.update { it.copy(isSubmitting = false, isSuccess = true) }
                },
                onFailure = { err ->
                    _uiState.update { it.copy(isSubmitting = false, errorMessage = err.message ?: "Opening stock failed") }
                }
            )
        }
    }
}
