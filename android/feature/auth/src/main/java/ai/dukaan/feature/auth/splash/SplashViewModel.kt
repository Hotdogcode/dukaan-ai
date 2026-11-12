package ai.dukaan.feature.auth.splash

import ai.dukaan.core.domain.repository.AuthRepository
import ai.dukaan.core.domain.repository.BusinessRepository
import ai.dukaan.core.domain.usecase.GetAppConfigUseCase
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SplashViewModel @Inject constructor(
    private val getAppConfigUseCase: GetAppConfigUseCase,
    private val authRepository: AuthRepository,
    private val businessRepository: BusinessRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow<SplashUiState>(SplashUiState.Loading)
    val uiState: StateFlow<SplashUiState> = _uiState.asStateFlow()

    init {
        restoreSession()
    }

    fun restoreSession() {
        viewModelScope.launch {
            val appConfig = getAppConfigUseCase().first()

            // 1. Check if an authenticated access token is present
            val isAuth = authRepository.isAuthenticated().first()
            if (!isAuth) {
                // Try refresh token if present in secure storage
                val refreshResult = authRepository.refreshToken()
                if (refreshResult.isFailure) {
                    _uiState.value = SplashUiState.Success(SplashTarget.LOGIN)
                    return@launch
                }
            }

            // 2. Query businesses to determine if merchant needs onboarding or has active store
            val businessesResult = businessRepository.getMyBusinesses()
            businessesResult.fold(
                onSuccess = { memberships ->
                    if (memberships.isEmpty()) {
                        _uiState.value = SplashUiState.Success(SplashTarget.ONBOARDING)
                    } else {
                        _uiState.value = SplashUiState.Success(SplashTarget.DASHBOARD)
                    }
                },
                onFailure = {
                    // Offline resilience: If offline and cached selectedBusinessId exists, route to Dashboard
                    if (appConfig.selectedBusinessId != null || appConfig.isOnboardingCompleted) {
                        _uiState.value = SplashUiState.Success(SplashTarget.DASHBOARD)
                    } else {
                        _uiState.value = SplashUiState.Success(SplashTarget.LOGIN)
                    }
                },
            )
        }
    }
}
