package ai.dukaan.core.domain.repository

import ai.dukaan.core.model.AuthTokens
import ai.dukaan.core.model.OtpRequestResult
import ai.dukaan.core.model.User
import kotlinx.coroutines.flow.Flow

/**
 * Domain repository contract for phone OTP authentication, session management, and JWT tokens.
 */
interface AuthRepository {
    suspend fun requestOtp(phoneNumber: String): Result<OtpRequestResult>
    suspend fun verifyOtp(
        phoneNumber: String?,
        otp: String,
        requestId: String? = null,
        fullName: String? = null,
    ): Result<Pair<User, AuthTokens>>
    suspend fun refreshToken(): Result<AuthTokens>
    suspend fun logout(): Result<Unit>
    fun getCurrentUser(): Flow<User?>
    fun isAuthenticated(): Flow<Boolean>
}
