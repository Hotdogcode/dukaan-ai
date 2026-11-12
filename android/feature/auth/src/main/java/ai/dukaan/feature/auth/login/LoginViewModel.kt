package ai.dukaan.feature.auth.login

import ai.dukaan.core.domain.usecase.RequestOtpUseCase
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class LoginUiState(
    val phoneNumber: String = "",
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val isOtpRequested: Boolean = false,
    val requestId: String? = null,
)

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val requestOtpUseCase: RequestOtpUseCase,
) : ViewModel() {

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    fun onPhoneNumberChanged(phoneNumber: String) {
        var digits = phoneNumber.filter { it.isDigit() }
        if (digits.startsWith("91") && digits.length > 10) {
            digits = digits.drop(2)
        }
        val sanitized = digits.take(10)
        _uiState.update { it.copy(phoneNumber = sanitized, errorMessage = null) }
    }

    fun requestOtp(onSuccess: (phoneNumber: String, requestId: String?) -> Unit) {
        val phone = _uiState.value.phoneNumber.trim()
        if (phone.length != 10 || !phone.first().isDigit() || phone.first() !in listOf('6', '7', '8', '9')) {
            _uiState.update {
                it.copy(errorMessage = "Please enter a valid 10-digit Indian mobile number")
            }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            val result = requestOtpUseCase(phone)
            result.fold(
                onSuccess = { otpResult ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            isOtpRequested = true,
                            requestId = otpResult.requestId,
                        )
                    }
                    onSuccess(phone, otpResult.requestId)
                },
                onFailure = { error ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = error.localizedMessage ?: "Failed to dispatch OTP. Please check your network and retry.",
                        )
                    }
                },
            )
        }
    }
}
