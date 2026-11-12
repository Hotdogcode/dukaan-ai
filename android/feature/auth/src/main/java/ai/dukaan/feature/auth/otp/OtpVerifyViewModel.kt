package ai.dukaan.feature.auth.otp

import ai.dukaan.core.domain.usecase.GetMyBusinessesUseCase
import ai.dukaan.core.domain.usecase.RequestOtpUseCase
import ai.dukaan.core.domain.usecase.VerifyOtpUseCase
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class OtpVerifyUiState(
    val phoneNumber: String = "",
    val requestId: String? = null,
    val otpCode: String = "",
    val countdownSeconds: Int = 30,
    val canResend: Boolean = false,
    val isLoading: Boolean = false,
    val isResending: Boolean = false,
    val errorMessage: String? = null,
)

@HiltViewModel
class OtpVerifyViewModel @Inject constructor(
    private val verifyOtpUseCase: VerifyOtpUseCase,
    private val requestOtpUseCase: RequestOtpUseCase,
    private val getMyBusinessesUseCase: GetMyBusinessesUseCase,
) : ViewModel() {

    private val _uiState = MutableStateFlow(OtpVerifyUiState())
    val uiState: StateFlow<OtpVerifyUiState> = _uiState.asStateFlow()

    private var countdownJob: Job? = null

    fun initialize(phoneNumber: String, requestId: String?) {
        _uiState.update {
            it.copy(
                phoneNumber = phoneNumber,
                requestId = requestId,
            )
        }
        startCountdownTimer()
    }

    private fun startCountdownTimer() {
        countdownJob?.cancel()
        countdownJob = viewModelScope.launch {
            for (sec in 30 downTo 0) {
                _uiState.update { it.copy(countdownSeconds = sec, canResend = sec == 0) }
                if (sec > 0) delay(1000L)
            }
        }
    }

    fun onOtpCodeChanged(code: String) {
        val sanitized = code.filter { it.isDigit() }.take(6)
        _uiState.update { it.copy(otpCode = sanitized, errorMessage = null) }
    }

    fun resendOtp() {
        val phone = _uiState.value.phoneNumber
        if (phone.isBlank()) return

        viewModelScope.launch {
            _uiState.update { it.copy(isResending = true, errorMessage = null) }
            val result = requestOtpUseCase(phone)
            result.fold(
                onSuccess = { res ->
                    _uiState.update {
                        it.copy(
                            isResending = false,
                            requestId = res.requestId,
                            otpCode = "",
                        )
                    }
                    startCountdownTimer()
                },
                onFailure = { error ->
                    _uiState.update {
                        it.copy(
                            isResending = false,
                            errorMessage = error.localizedMessage ?: "Failed to resend OTP. Please try again.",
                        )
                    }
                },
            )
        }
    }

    fun verifyOtp(
        onNavigateToOnboarding: () -> Unit,
        onNavigateToDashboard: () -> Unit,
    ) {
        val state = _uiState.value
        if (state.otpCode.length != 6) {
            _uiState.update { it.copy(errorMessage = "Please enter the full 6-digit OTP code") }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            val verifyResult = verifyOtpUseCase(
                phoneNumber = state.phoneNumber,
                otp = state.otpCode,
                requestId = state.requestId,
            )

            verifyResult.fold(
                onSuccess = {
                    // Check businesses to route either to Onboarding or Dashboard
                    val businessesResult = getMyBusinessesUseCase()
                    _uiState.update { it.copy(isLoading = false) }
                    businessesResult.fold(
                        onSuccess = { memberships ->
                            if (memberships.isEmpty()) {
                                onNavigateToOnboarding()
                            } else {
                                onNavigateToDashboard()
                            }
                        },
                        onFailure = {
                            // If fetching businesses fails (e.g. initial account creation), proceed to onboarding
                            onNavigateToOnboarding()
                        },
                    )
                },
                onFailure = { error ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = error.localizedMessage ?: "Invalid OTP code. Please check and try again.",
                        )
                    }
                },
            )
        }
    }

    override fun onCleared() {
        super.onCleared()
        countdownJob?.cancel()
    }
}
