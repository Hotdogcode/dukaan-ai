package ai.dukaan.core.domain.usecase

import ai.dukaan.core.domain.repository.AppConfigRepository

class SetOnboardingCompletedUseCase(
    private val appConfigRepository: AppConfigRepository,
) {
    suspend operator fun invoke(completed: Boolean = true) {
        appConfigRepository.setOnboardingCompleted(completed)
    }
}
