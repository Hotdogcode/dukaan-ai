package ai.dukaan.core.domain.usecase

import ai.dukaan.core.domain.repository.AuthRepository
import ai.dukaan.core.model.OtpRequestResult

class RequestOtpUseCase(
    private val authRepository: AuthRepository,
) {
    suspend operator fun invoke(phoneNumber: String): Result<OtpRequestResult> {
        return authRepository.requestOtp(phoneNumber)
    }
}
