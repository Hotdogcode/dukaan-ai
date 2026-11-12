package ai.dukaan.core.network.interceptor

import okhttp3.Interceptor
import okhttp3.Response
import timber.log.Timber
import java.io.IOException
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Safe HTTP logger that logs request URLs, methods, status codes, and latency,
 * but scrubs sensitive headers (Authorization, Cookie) and sensitive endpoints (OTP, Auth).
 */
@Singleton
class SafeLoggingInterceptor @Inject constructor() : Interceptor {

    private val sensitivePaths = listOf("/auth/otp", "/auth/token", "/auth/login", "/auth/verify")

    @Throws(IOException::class)
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val url = request.url.toString()
        val path = request.url.encodedPath
        val method = request.method
        val startNs = System.nanoTime()

        val isSensitive = sensitivePaths.any { path.contains(it, ignoreCase = true) }

        Timber.d("--> HTTP $method $url ${if (isSensitive) "[SENSITIVE AUTH ENDPOINT]" else ""}")

        val response: Response
        try {
            response = chain.proceed(request)
        } catch (e: Exception) {
            Timber.w("<-- HTTP $method $url FAILED: ${e.message}")
            throw e
        }

        val tookMs = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - startNs)
        Timber.d("<-- HTTP ${response.code} ${response.message} $url (${tookMs}ms)")

        return response
    }
}
