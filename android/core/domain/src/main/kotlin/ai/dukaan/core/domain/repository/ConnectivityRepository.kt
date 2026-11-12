package ai.dukaan.core.domain.repository

import ai.dukaan.core.model.ConnectivityStatus
import kotlinx.coroutines.flow.Flow

interface ConnectivityRepository {
    fun observeConnectivity(): Flow<ConnectivityStatus>
}
