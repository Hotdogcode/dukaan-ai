package ai.dukaan.core.network.interceptor

import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Interface allowing secure token & business ID retrieval for network requests.
 */
interface AuthTokenProvider {
    fun getAccessToken(): String?
    fun getActiveBusinessId(): String?
}

/**
 * Attaches Authorization Bearer token and X-Business-ID headers when available.
 */
@Singleton
class AuthInterceptor @Inject constructor(
    private val tokenProvider: AuthTokenProvider,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val builder = originalRequest.newBuilder()

        val token = tokenProvider.getAccessToken()
        if (!token.isNullOrBlank() && originalRequest.header(HEADER_AUTHORIZATION) == null) {
            builder.header(HEADER_AUTHORIZATION, "Bearer $token")
        }

        val businessId = tokenProvider.getActiveBusinessId()
        if (!businessId.isNullOrBlank() && originalRequest.header(HEADER_BUSINESS_ID) == null) {
            builder.header(HEADER_BUSINESS_ID, businessId)
        }

        return chain.proceed(builder.build())
    }

    companion object {
        const val HEADER_AUTHORIZATION = "Authorization"
        const val HEADER_BUSINESS_ID = "X-Business-ID"
    }
}
