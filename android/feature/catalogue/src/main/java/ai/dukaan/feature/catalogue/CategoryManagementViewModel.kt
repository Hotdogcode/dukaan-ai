package ai.dukaan.feature.catalogue

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.domain.repository.CatalogueRepository
import ai.dukaan.core.model.Category
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

data class CategoryManagementUiState(
    val isCreating: Boolean = false,
    val showCreateDialog: Boolean = false,
    val errorMessage: String? = null,
    val successMessage: String? = null,
)

@HiltViewModel
class CategoryManagementViewModel @Inject constructor(
    private val appConfigRepository: AppConfigRepository,
    private val catalogueRepository: CatalogueRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(CategoryManagementUiState())
    val uiState: StateFlow<CategoryManagementUiState> = _uiState.asStateFlow()

    val businessId: StateFlow<UUID?> = appConfigRepository.appConfig
        .map { it.selectedBusinessId }
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val categories: StateFlow<List<Category>> = businessId
        .flatMapLatest { bId ->
            if (bId == null) flowOf(emptyList())
            else catalogueRepository.getCategories(bId, activeOnly = false)
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    fun openCreateDialog() = _uiState.update { it.copy(showCreateDialog = true) }
    fun closeCreateDialog() = _uiState.update { it.copy(showCreateDialog = false) }

    fun createCategory(name: String, description: String?, parentId: UUID?) {
        val cleanName = name.trim()
        if (cleanName.isBlank()) {
            _uiState.update { it.copy(errorMessage = "Category name cannot be blank") }
            return
        }

        val bId = businessId.value ?: run {
            _uiState.update { it.copy(errorMessage = "Missing business context") }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isCreating = true, errorMessage = null) }
            val result = catalogueRepository.createCategory(
                businessId = bId,
                name = cleanName,
                description = description?.ifBlank { null },
                parentId = parentId,
            )
            _uiState.update {
                it.copy(
                    isCreating = false,
                    showCreateDialog = !result.isSuccess,
                    successMessage = if (result.isSuccess) "Category \"$cleanName\" created" else null,
                    errorMessage = result.exceptionOrNull()?.message,
                )
            }
        }
    }

    fun clearMessages() = _uiState.update { it.copy(errorMessage = null, successMessage = null) }
}
