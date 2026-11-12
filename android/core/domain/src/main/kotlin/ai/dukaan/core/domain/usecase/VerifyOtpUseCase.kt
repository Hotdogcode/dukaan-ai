package ai.dukaan.core.domain.usecase

import ai.dukaan.core.domain.repository.AuthRepository
import ai.dukaan.core.model.AuthTokens
import ai.dukaan.core.model.User

class VerifyOtpUseCase(
    private val authRepository: AuthRepository,
) {
    suspend operator fun invoke(
        phoneNumber: String?,
        otp: String,
        requestId: String? = null,
        fullName: String? = null,
    ): Result<Pair<User, AuthTokens>> {
        return authRepository.verifyOtp(
            phoneNumber = phoneNumber,
            otp = otp,
            requestId = requestId,
            fullName = fullName,
        )
    }
}
