package ai.dukaan.core.testing.repository

import ai.dukaan.core.domain.repository.ConnectivityRepository
import ai.dukaan.core.model.ConnectivityStatus
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class FakeConnectivityRepository : ConnectivityRepository {
    private val _status = MutableStateFlow(ConnectivityStatus.AVAILABLE)

    override fun observeConnectivity(): Flow<ConnectivityStatus> = _status.asStateFlow()

    fun setStatus(status: ConnectivityStatus) {
        _status.value = status
    }
}
