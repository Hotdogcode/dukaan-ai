package ai.dukaan.feature.onboarding

import ai.dukaan.core.domain.usecase.CreateBusinessUseCase
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class BusinessOnboardingUiState(
    val businessName: String = "",
    val businessType: String = "GROCERY",
    val ownerName: String = "",
    val preferredLanguage: String = "hi",
    val storeName: String = "",
    val city: String = "Mumbai",
    val state: String = "Maharashtra",
    val pincode: String = "400001",
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
)

@HiltViewModel
class BusinessOnboardingViewModel @Inject constructor(
    private val createBusinessUseCase: CreateBusinessUseCase,
) : ViewModel() {

    private val _uiState = MutableStateFlow(BusinessOnboardingUiState())
    val uiState: StateFlow<BusinessOnboardingUiState> = _uiState.asStateFlow()

    fun onBusinessNameChanged(name: String) {
        _uiState.update { it.copy(businessName = name, errorMessage = null) }
    }

    fun onBusinessTypeChanged(type: String) {
        _uiState.update { it.copy(businessType = type) }
    }

    fun onOwnerNameChanged(name: String) {
        _uiState.update { it.copy(ownerName = name, errorMessage = null) }
    }

    fun onLanguageChanged(lang: String) {
        _uiState.update { it.copy(preferredLanguage = lang) }
    }

    fun onStoreNameChanged(name: String) {
        _uiState.update { it.copy(storeName = name) }
    }

    fun onCityChanged(city: String) {
        _uiState.update { it.copy(city = city) }
    }

    fun onStateChanged(state: String) {
        _uiState.update { it.copy(state = state) }
    }

    fun onPincodeChanged(pincode: String) {
        val sanitized = pincode.filter { it.isDigit() }.take(6)
        _uiState.update { it.copy(pincode = sanitized) }
    }

    fun submitOnboarding(onSuccess: () -> Unit) {
        val state = _uiState.value
        val name = state.businessName.trim()
        if (name.length < 2) {
            _uiState.update { it.copy(errorMessage = "Business name must be at least 2 characters") }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            val initialStore = state.storeName.trim().ifBlank { "$name Main Store" }
            val result = createBusinessUseCase(
                name = name,
                businessType = state.businessType,
                ownerName = state.ownerName.trim().ifBlank { null },
                language = state.preferredLanguage,
                initialStoreName = initialStore,
            )

            result.fold(
                onSuccess = {
                    _uiState.update { it.copy(isLoading = false) }
                    onSuccess()
                },
                onFailure = { error ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = error.localizedMessage ?: "Failed to set up business profile. Please retry.",
                        )
                    }
                },
            )
        }
    }
}
