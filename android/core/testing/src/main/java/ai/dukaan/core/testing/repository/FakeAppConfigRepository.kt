package ai.dukaan.core.testing.repository

import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.model.AppConfig
import ai.dukaan.core.model.ThemePreference
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import java.util.UUID

class FakeAppConfigRepository : AppConfigRepository {

    private val _appConfig = MutableStateFlow(AppConfig())
    override val appConfig: Flow<AppConfig> = _appConfig.asStateFlow()

    override suspend fun setSelectedBusinessId(businessId: UUID?) {
        _appConfig.update { it.copy(selectedBusinessId = businessId) }
    }

    override suspend fun setSelectedStoreId(storeId: UUID?) {
        _appConfig.update { it.copy(selectedStoreId = storeId) }
    }

    override suspend fun setThemePreference(theme: ThemePreference) {
        _appConfig.update { it.copy(theme = theme) }
    }

    override suspend fun setLanguagePreference(language: String) {
        _appConfig.update { it.copy(language = language) }
    }

    override suspend fun setOnboardingCompleted(completed: Boolean) {
        _appConfig.update { it.copy(isOnboardingCompleted = completed) }
    }
}
