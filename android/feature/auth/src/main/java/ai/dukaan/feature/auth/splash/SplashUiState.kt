package ai.dukaan.feature.auth.splash

import ai.dukaan.core.ui.UiState

sealed interface SplashUiState : UiState {
    data object Loading : SplashUiState
    data class Success(val destination: SplashTarget) : SplashUiState
}

enum class SplashTarget {
    LOGIN,
    ONBOARDING,
    DASHBOARD,
}
