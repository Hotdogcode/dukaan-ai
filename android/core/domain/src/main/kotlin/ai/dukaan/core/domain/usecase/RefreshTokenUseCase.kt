package ai.dukaan.core.domain.usecase

import ai.dukaan.core.domain.repository.AuthRepository
import ai.dukaan.core.model.AuthTokens

class RefreshTokenUseCase(
    private val authRepository: AuthRepository,
) {
    suspend operator fun invoke(): Result<AuthTokens> {
        return authRepository.refreshToken()
    }
}
