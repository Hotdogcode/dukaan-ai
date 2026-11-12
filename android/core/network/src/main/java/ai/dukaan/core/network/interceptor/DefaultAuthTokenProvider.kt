package ai.dukaan.core.network.interceptor

import ai.dukaan.core.network.token.SecureTokenStorage
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DefaultAuthTokenProvider @Inject constructor(
    private val secureTokenStorage: SecureTokenStorage,
) : AuthTokenProvider {

    @Volatile
    private var activeBusinessId: String? = null

    fun setActiveBusinessId(businessId: String?) {
        activeBusinessId = businessId
    }

    override fun getAccessToken(): String? = secureTokenStorage.getAccessToken()

    override fun getActiveBusinessId(): String? = activeBusinessId
}
