package ai.dukaan.core.domain.usecase

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.model.AppConfig
import kotlinx.coroutines.flow.Flow

class GetAppConfigUseCase(
    private val appConfigRepository: AppConfigRepository,
) {
    operator fun invoke(): Flow<AppConfig> = appConfigRepository.appConfig
}
