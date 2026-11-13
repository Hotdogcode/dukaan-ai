package ai.dukaan.feature.inventory

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.domain.repository.InventoryRepository
import ai.dukaan.core.model.InventoryCountSession
import ai.dukaan.core.model.InventoryItem
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

data class StockCountUiState(
    val activeSession: InventoryCountSession? = null,
    val selectedVariantId: UUID? = null,
    val selectedVariantName: String = "",
    val expectedQuantity: BigDecimal = BigDecimal.ZERO,
    val countedQuantityText: String = "",
    val countNotesText: String = "",
    val isSubmitting: Boolean = false,
    val errorMessage: String? = null,
    val successMessage: String? = null,
) {
    val countedQuantity: BigDecimal?
        get() = countedQuantityText.toBigDecimalOrNull()

    val variance: BigDecimal
        get() = (countedQuantity ?: BigDecimal.ZERO) - expectedQuantity
}

@OptIn(ExperimentalCoroutinesApi::class)
@HiltViewModel
class StockCountViewModel @Inject constructor(
    private val appConfigRepository: AppConfigRepository,
    private val inventoryRepository: InventoryRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(StockCountUiState())
    val uiState: StateFlow<StockCountUiState> = _uiState.asStateFlow()

    private val contextFlow = appConfigRepository.appConfig
        .distinctUntilChanged()
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val countSessions: StateFlow<List<InventoryCountSession>> = contextFlow
        .flatMapLatest { config ->
            val bId = config?.selectedBusinessId
            val sId = config?.selectedStoreId
            if (bId != null && sId != null) {
                inventoryRepository.getCountSessions(bId, sId)
            } else {
                flowOf(emptyList())
            }
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

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

    fun createSession() {
        val config = contextFlow.value ?: return
        val bId = config.selectedBusinessId ?: return
        val sId = config.selectedStoreId ?: return

        viewModelScope.launch {
            _uiState.update { it.copy(isSubmitting = true, errorMessage = null) }
            val res = inventoryRepository.createCountSession(bId, sId, notes = "Store physical count audit")
            res.fold(
                onSuccess = { session ->
                    _uiState.update { it.copy(isSubmitting = false, activeSession = session, successMessage = "Started ${session.sessionNumber}") }
                },
                onFailure = { err ->
                    _uiState.update { it.copy(isSubmitting = false, errorMessage = err.message ?: "Failed to start count session") }
                }
            )
        }
    }

    fun openSession(sessionId: UUID) {
        val config = contextFlow.value ?: return
        val bId = config.selectedBusinessId ?: return
        val sId = config.selectedStoreId ?: return

        viewModelScope.launch {
            _uiState.update { it.copy(isSubmitting = true) }
            val res = inventoryRepository.getCountSession(bId, sId, sessionId)
            res.fold(
                onSuccess = { session ->
                    _uiState.update { it.copy(isSubmitting = false, activeSession = session) }
                },
                onFailure = { err ->
                    _uiState.update { it.copy(isSubmitting = false, errorMessage = err.message ?: "Failed to load session") }
                }
            )
        }
    }

    fun onSelectVariant(variantId: UUID, name: String, currentQty: BigDecimal) {
        _uiState.update {
            it.copy(
                selectedVariantId = variantId,
                selectedVariantName = name,
                expectedQuantity = currentQty,
                countedQuantityText = "",
            )
        }
    }

    fun onCountedQuantityChange(text: String) {
        _uiState.update { it.copy(countedQuantityText = text) }
    }

    fun onCountNotesChange(text: String) {
        _uiState.update { it.copy(countNotesText = text) }
    }

    fun recordCountItem() {
        val s = _uiState.value
        val config = contextFlow.value ?: return
        val bId = config.selectedBusinessId ?: return
        val sId = config.selectedStoreId ?: return
        val session = s.activeSession ?: return
        val vId = s.selectedVariantId ?: return
        val countedQty = s.countedQuantity ?: return

        viewModelScope.launch {
            _uiState.update { it.copy(isSubmitting = true, errorMessage = null) }
            val res = inventoryRepository.recordCountItem(
                businessId = bId,
                storeId = sId,
                sessionId = session.id,
                variantId = vId,
                countedQuantity = countedQty,
                notes = s.countNotesText.ifBlank { null }
            )
            res.fold(
                onSuccess = {
                    // Reload active session
                    val reloaded = inventoryRepository.getCountSession(bId, sId, session.id)
                    _uiState.update {
                        it.copy(
                            isSubmitting = false,
                            activeSession = reloaded.getOrNull() ?: it.activeSession,
                            countedQuantityText = "",
                            selectedVariantId = null,
                            selectedVariantName = "",
                            successMessage = "Recorded count variance: ${s.variance} units"
                        )
                    }
                },
                onFailure = { err ->
                    _uiState.update { it.copy(isSubmitting = false, errorMessage = err.message ?: "Failed to record item") }
                }
            )
        }
    }

    fun completeSession() {
        val s = _uiState.value
        val config = contextFlow.value ?: return
        val bId = config.selectedBusinessId ?: return
        val sId = config.selectedStoreId ?: return
        val session = s.activeSession ?: return

        viewModelScope.launch {
            _uiState.update { it.copy(isSubmitting = true, errorMessage = null) }
            val res = inventoryRepository.completeCountSession(bId, sId, session.id)
            res.fold(
                onSuccess = {
                    _uiState.update {
                        it.copy(
                            isSubmitting = false,
                            activeSession = null,
                            successMessage = "Audit session finalized. Variance movements posted to ledger.",
                        )
                    }
                },
                onFailure = { err ->
                    _uiState.update { it.copy(isSubmitting = false, errorMessage = err.message ?: "Failed to complete audit") }
                }
            )
        }
    }

    fun closeActiveSession() {
        _uiState.update { it.copy(activeSession = null) }
    }

    fun clearMessages() {
        _uiState.update { it.copy(errorMessage = null, successMessage = null) }
    }
}
