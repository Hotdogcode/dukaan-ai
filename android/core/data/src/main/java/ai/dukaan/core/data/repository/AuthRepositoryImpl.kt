package ai.dukaan.core.data.repository

import ai.dukaan.core.datastore.UserPreferencesDataSource
import ai.dukaan.core.domain.repository.AuthRepository
import ai.dukaan.core.model.AuthTokens
import ai.dukaan.core.model.OtpRequestResult
import ai.dukaan.core.model.User
import ai.dukaan.core.network.api.AuthApiService
import ai.dukaan.core.network.model.LogoutNetwork
import ai.dukaan.core.network.model.OtpRequestNetwork
import ai.dukaan.core.network.model.OtpVerifyNetwork
import ai.dukaan.core.network.model.RefreshTokenNetwork
import ai.dukaan.core.network.token.SecureTokenStorage
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import timber.log.Timber
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val authApiService: AuthApiService,
    private val secureTokenStorage: SecureTokenStorage,
    private val userPreferencesDataSource: UserPreferencesDataSource,
) : AuthRepository {

    override suspend fun requestOtp(phoneNumber: String): Result<OtpRequestResult> = runCatching {
        val response = authApiService.requestOtp(OtpRequestNetwork(phoneNumber = phoneNumber))
        if (!response.isSuccessful) {
            val errorBody = response.errorBody()?.string()
            throw RuntimeException("Failed to request OTP: HTTP ${response.code()} $errorBody")
        }
        val body = response.body() ?: throw RuntimeException("Empty response body from OTP request")
        OtpRequestResult(
            requestId = body.requestId,
            phoneNumber = body.phoneNumber,
            expiresInSeconds = body.expiresInSeconds,
            retryAfterSeconds = body.retryAfterSeconds,
            message = body.message,
        )
    }

    override suspend fun verifyOtp(
        phoneNumber: String?,
        otp: String,
        requestId: String?,
        fullName: String?,
    ): Result<Pair<User, AuthTokens>> = runCatching {
        val payload = OtpVerifyNetwork(
            otp = otp,
            phoneNumber = phoneNumber,
            requestId = requestId,
            fullName = fullName,
        )
        val response = authApiService.verifyOtp(payload)
        if (!response.isSuccessful) {
            val errorBody = response.errorBody()?.string()
            throw RuntimeException("Failed to verify OTP: HTTP ${response.code()} $errorBody")
        }
        val body = response.body() ?: throw RuntimeException("Empty response body from OTP verification")

        val tokens = AuthTokens(
            accessToken = body.accessToken,
            refreshToken = body.refreshToken,
            tokenType = body.tokenType,
            expiresIn = body.expiresIn,
        )
        secureTokenStorage.saveTokens(tokens)

        val userId = runCatching { UUID.fromString(body.user.id) }.getOrDefault(UUID.randomUUID())
        val user = User(
            id = userId,
            phoneNumber = body.user.phoneNumber,
            fullName = body.user.fullName,
            isActive = body.user.isActive,
        )
        userPreferencesDataSource.setUserProfile(
            userId = user.id,
            phoneNumber = user.phoneNumber,
            fullName = user.fullName,
        )

        Pair(user, tokens)
    }

    override suspend fun refreshToken(): Result<AuthTokens> = runCatching {
        val currentRefresh = secureTokenStorage.getRefreshToken()
            ?: throw IllegalStateException("No refresh token available")

        val response = authApiService.refreshToken(RefreshTokenNetwork(refreshToken = currentRefresh))
        if (!response.isSuccessful) {
            secureTokenStorage.clearTokens()
            throw RuntimeException("Token refresh rejected: HTTP ${response.code()}")
        }
        val body = response.body() ?: throw RuntimeException("Empty response from token refresh")
        val newTokens = AuthTokens(
            accessToken = body.accessToken,
            refreshToken = body.refreshToken,
            tokenType = body.tokenType,
            expiresIn = body.expiresIn,
        )
        secureTokenStorage.saveTokens(newTokens)
        newTokens
    }

    override suspend fun logout(): Result<Unit> = runCatching {
        val refresh = secureTokenStorage.getRefreshToken()
        if (!refresh.isNullOrBlank()) {
            try {
                authApiService.logout(LogoutNetwork(refreshToken = refresh))
            } catch (e: Exception) {
                Timber.w(e, "Logout call to backend failed, proceeding with local purge")
            }
        }
        secureTokenStorage.clearTokens()
        userPreferencesDataSource.clearSession()
    }

    override fun getCurrentUser(): Flow<User?> {
        return userPreferencesDataSource.appConfig.map { config ->
            val userId = config.userId
            val phone = config.userPhoneNumber
            if (userId != null && phone != null) {
                User(
                    id = userId,
                    phoneNumber = phone,
                    fullName = config.userFullName,
                    isActive = true,
                )
            } else {
                null
            }
        }
    }

    override fun isAuthenticated(): Flow<Boolean> {
        return userPreferencesDataSource.appConfig.map { config ->
            config.userId != null && secureTokenStorage.getAccessToken() != null
        }
    }
}
