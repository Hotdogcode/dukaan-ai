package ai.dukaan.core.network.interceptor

import okhttp3.Interceptor
import okhttp3.Response
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Propagates or generates an X-Request-ID header on all outbound HTTP network requests
 * for distributed tracing and correlation with backend FastAPI request logs.
 */
@Singleton
class RequestIdInterceptor @Inject constructor() : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val requestWithId = if (originalRequest.header(HEADER_REQUEST_ID) == null) {
            originalRequest.newBuilder()
                .header(HEADER_REQUEST_ID, UUID.randomUUID().toString())
                .build()
        } else {
            originalRequest
        }
        return chain.proceed(requestWithId)
    }

    companion object {
        const val HEADER_REQUEST_ID = "X-Request-ID"
    }
}
