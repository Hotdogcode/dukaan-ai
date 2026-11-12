package ai.dukaan.core.data.repository

import ai.dukaan.core.domain.repository.ConnectivityRepository
import ai.dukaan.core.model.ConnectivityStatus
import ai.dukaan.core.network.connectivity.ConnectivityObserver
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ConnectivityRepositoryImpl @Inject constructor(
    private val connectivityObserver: ConnectivityObserver,
) : ConnectivityRepository {

    override fun observeConnectivity(): Flow<ConnectivityStatus> =
        connectivityObserver.observe()
}
