package ai.dukaan.core.testing.repository

import ai.dukaan.core.domain.repository.AuthRepository
import ai.dukaan.core.model.AuthTokens
import ai.dukaan.core.model.OtpRequestResult
import ai.dukaan.core.model.User
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.UUID

class FakeAuthRepository : AuthRepository {

    private val currentUser = MutableStateFlow<User?>(null)
    private val isAuth = MutableStateFlow(false)

    var shouldOtpRequestSucceed: Boolean = true
    var shouldVerifySucceed: Boolean = true
    var shouldRefreshSucceed: Boolean = true

    fun setAuthenticated(authenticated: Boolean, user: User? = null) {
        isAuth.value = authenticated
        currentUser.value = user
    }

    override suspend fun requestOtp(phoneNumber: String): Result<OtpRequestResult> {
        return if (shouldOtpRequestSucceed) {
            Result.success(
                OtpRequestResult(
                    requestId = "fake-req-${UUID.randomUUID()}",
                    phoneNumber = phoneNumber,
                    expiresInSeconds = 300,
                    retryAfterSeconds = 30,
                    message = "OTP sent",
                )
            )
        } else {
            Result.failure(RuntimeException("Network error requesting OTP"))
        }
    }

    override suspend fun verifyOtp(
        phoneNumber: String?,
        otp: String,
        requestId: String?,
        fullName: String?,
    ): Result<Pair<User, AuthTokens>> {
        return if (shouldVerifySucceed) {
            val user = User(
                id = UUID.randomUUID(),
                phoneNumber = phoneNumber ?: "+919876543210",
                fullName = fullName ?: "Test Merchant",
                isActive = true,
            )
            val tokens = AuthTokens(
                accessToken = "fake-jwt-access-token",
                refreshToken = "fake-jwt-refresh-token",
            )
            setAuthenticated(true, user)
            Result.success(Pair(user, tokens))
        } else {
            Result.failure(RuntimeException("Invalid OTP code"))
        }
    }

    override suspend fun refreshToken(): Result<AuthTokens> {
        return if (shouldRefreshSucceed) {
            val tokens = AuthTokens(
                accessToken = "fake-refreshed-jwt-access-token",
                refreshToken = "fake-refreshed-jwt-refresh-token",
            )
            isAuth.value = true
            Result.success(tokens)
        } else {
            isAuth.value = false
            Result.failure(RuntimeException("Refresh token expired"))
        }
    }

    override suspend fun logout(): Result<Unit> {
        setAuthenticated(false, null)
        return Result.success(Unit)
    }

    override fun getCurrentUser(): Flow<User?> = currentUser.asStateFlow()

    override fun isAuthenticated(): Flow<Boolean> = isAuth.asStateFlow()
}
