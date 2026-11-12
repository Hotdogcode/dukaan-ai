package ai.dukaan.core.domain.usecase

import ai.dukaan.core.domain.repository.ConnectivityRepository
import ai.dukaan.core.model.ConnectivityStatus
import kotlinx.coroutines.flow.Flow

class ObserveConnectivityUseCase(
    private val connectivityRepository: ConnectivityRepository,
) {
    operator fun invoke(): Flow<ConnectivityStatus> = connectivityRepository.observeConnectivity()
}
