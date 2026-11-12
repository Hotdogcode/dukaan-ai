package ai.dukaan.feature.dashboard

import ai.dukaan.core.domain.usecase.GetAppConfigUseCase
import ai.dukaan.core.domain.usecase.ObserveConnectivityUseCase
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

@HiltViewModel
class DashboardViewModel @Inject constructor(
    getAppConfigUseCase: GetAppConfigUseCase,
    observeConnectivityUseCase: ObserveConnectivityUseCase,
) : ViewModel() {

    val uiState: StateFlow<DashboardUiState> = combine(
        getAppConfigUseCase(),
        observeConnectivityUseCase(),
    ) { config, connectivity ->
        DashboardUiState(
            appConfig = config,
            connectivityStatus = connectivity,
            isLoading = false,
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = DashboardUiState(isLoading = true),
    )
}
