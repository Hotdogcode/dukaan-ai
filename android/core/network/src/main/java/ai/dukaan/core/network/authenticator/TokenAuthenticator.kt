package ai.dukaan.core.network.authenticator

import ai.dukaan.core.model.AuthTokens
import ai.dukaan.core.network.interceptor.AuthInterceptor.Companion.HEADER_AUTHORIZATION
import ai.dukaan.core.network.model.RefreshTokenNetwork
import ai.dukaan.core.network.model.TokenResponseNetwork
import ai.dukaan.core.network.token.SecureTokenStorage
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.Json
import okhttp3.Authenticator
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okhttp3.Route
import timber.log.Timber
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TokenAuthenticator @Inject constructor(
    private val secureTokenStorage: SecureTokenStorage,
    private val json: Json,
) : Authenticator {

    private val refreshMutex = Mutex()

    private val refreshClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .build()
    }

    override fun authenticate(route: Route?, response: Response): Request? {
        if (responseCount(response) >= 3) {
            Timber.w("Max 401 authentication retry count reached. Aborting.")
            return null
        }

        val requestPath = response.request.url.encodedPath
        if (requestPath.contains("api/v1/auth/otp/") || requestPath.contains("api/v1/auth/refresh")) {
            return null
        }

        val originalAuthHeader = response.request.header(HEADER_AUTHORIZATION)

        return runBlocking {
            refreshMutex.withLock {
                val currentAccessToken = secureTokenStorage.getAccessToken()

                // If already refreshed by another concurrent call while waiting for mutex lock
                if (currentAccessToken != null && originalAuthHeader != "Bearer $currentAccessToken") {
                    Timber.d("Token was already refreshed by a concurrent request. Retrying with updated token.")
                    return@withLock response.request.newBuilder()
                        .header(HEADER_AUTHORIZATION, "Bearer $currentAccessToken")
                        .build()
                }

                val currentRefreshToken = secureTokenStorage.getRefreshToken()
                if (currentRefreshToken.isNullOrBlank()) {
                    Timber.w("No refresh token available. Session terminated.")
                    secureTokenStorage.clearTokens()
                    return@withLock null
                }

                val url = response.request.url
                val baseUrl = "${url.scheme}://${url.host}:${url.port}/"
                val newTokens = performRefresh(baseUrl, currentRefreshToken)
                if (newTokens != null) {
                    secureTokenStorage.saveTokens(newTokens)
                    response.request.newBuilder()
                        .header(HEADER_AUTHORIZATION, "Bearer ${newTokens.accessToken}")
                        .build()
                } else {
                    Timber.w("Refresh token revoked or invalid. Clearing secure tokens.")
                    secureTokenStorage.clearTokens()
                    null
                }
            }
        }
    }

    private fun performRefresh(baseUrl: String, refreshToken: String): AuthTokens? {
        return try {
            val payload = json.encodeToString(
                RefreshTokenNetwork.serializer(),
                RefreshTokenNetwork(refreshToken = refreshToken)
            )
            val requestBody = payload.toRequestBody("application/json".toMediaType())
            val request = Request.Builder()
                .url("${baseUrl}api/v1/auth/refresh")
                .post(requestBody)
                .build()

            val httpResponse = refreshClient.newCall(request).execute()
            if (httpResponse.isSuccessful) {
                val body = httpResponse.body?.string() ?: return null
                val tokenResponse = json.decodeFromString(TokenResponseNetwork.serializer(), body)
                AuthTokens(
                    accessToken = tokenResponse.accessToken,
                    refreshToken = tokenResponse.refreshToken,
                    tokenType = tokenResponse.tokenType,
                    expiresIn = tokenResponse.expiresIn,
                )
            } else {
                Timber.e("Token refresh call returned HTTP ${httpResponse.code}")
                null
            }
        } catch (e: Exception) {
            Timber.e(e, "Exception during token refresh")
            null
        }
    }

    private fun responseCount(response: Response): Int {
        var count = 1
        var prior = response.priorResponse
        while (prior != null) {
            count++
            prior = prior.priorResponse
        }
        return count
    }
}
