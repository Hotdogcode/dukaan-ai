package ai.dukaan.feature.dashboard

import ai.dukaan.core.model.AppConfig
import ai.dukaan.core.model.ConnectivityStatus
import ai.dukaan.core.ui.UiState

data class DashboardUiState(
    val appConfig: AppConfig = AppConfig(),
    val connectivityStatus: ConnectivityStatus = ConnectivityStatus.AVAILABLE,
    val isLoading: Boolean = false,
) : UiState
