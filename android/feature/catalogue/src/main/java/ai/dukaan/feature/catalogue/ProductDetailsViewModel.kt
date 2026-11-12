package ai.dukaan.feature.catalogue

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.domain.repository.CatalogueRepository
import ai.dukaan.core.domain.repository.ProductUpdateDraft
import ai.dukaan.core.model.Product
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

data class ProductDetailsUiState(
    val isLoading: Boolean = false,
    val isTogglingStatus: Boolean = false,
    val isAddingBarcode: Boolean = false,
    val errorMessage: String? = null,
    val successMessage: String? = null,
)

@HiltViewModel
class ProductDetailsViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val appConfigRepository: AppConfigRepository,
    private val catalogueRepository: CatalogueRepository,
) : ViewModel() {

    private val productIdString: String = checkNotNull(savedStateHandle["productId"])
    val productId: UUID = UUID.fromString(productIdString)

    private val _uiState = MutableStateFlow(ProductDetailsUiState())
    val uiState: StateFlow<ProductDetailsUiState> = _uiState.asStateFlow()

    val businessId: StateFlow<UUID?> = appConfigRepository.appConfig
        .map { it.selectedBusinessId }
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val product: StateFlow<Product?> = catalogueRepository.getProductById(productId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun toggleProductStatus() {
        val current = product.value ?: return
        val bId = businessId.value ?: return
        viewModelScope.launch {
            _uiState.update { it.copy(isTogglingStatus = true, errorMessage = null) }
            val newStatus = !current.isActive
            val updateDraft = ProductUpdateDraft(isActive = newStatus)
            val result = catalogueRepository.updateProduct(bId, productId, updateDraft)
            _uiState.update {
                it.copy(
                    isTogglingStatus = false,
                    successMessage = if (result.isSuccess) "Product marked as ${if (newStatus) "Active" else "Inactive"}" else null,
                    errorMessage = result.exceptionOrNull()?.message,
                )
            }
        }
    }

    fun addBarcode(barcode: String) {
        val clean = barcode.trim()
        if (clean.isBlank()) return
        val bId = businessId.value ?: return
        viewModelScope.launch {
            _uiState.update { it.copy(isAddingBarcode = true, errorMessage = null) }
            val result = catalogueRepository.registerBarcode(
                businessId = bId,
                barcode = clean,
                productId = productId,
            )
            _uiState.update {
                it.copy(
                    isAddingBarcode = false,
                    successMessage = if (result.isSuccess) "Barcode registered successfully" else null,
                    errorMessage = result.exceptionOrNull()?.message,
                )
            }
        }
    }

    fun clearMessages() {
        _uiState.update { it.copy(errorMessage = null, successMessage = null) }
    }
}
