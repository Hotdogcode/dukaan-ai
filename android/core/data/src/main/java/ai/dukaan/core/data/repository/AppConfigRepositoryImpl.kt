package ai.dukaan.core.data.repository

import ai.dukaan.core.datastore.UserPreferencesDataSource
import ai.dukaan.core.domain.repository.AppConfigRepository
import ai.dukaan.core.model.AppConfig
import ai.dukaan.core.model.ThemePreference
import kotlinx.coroutines.flow.Flow
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AppConfigRepositoryImpl @Inject constructor(
    private val userPreferencesDataSource: UserPreferencesDataSource,
) : AppConfigRepository {

    override val appConfig: Flow<AppConfig> = userPreferencesDataSource.appConfig

    override suspend fun setSelectedBusinessId(businessId: UUID?) {
        userPreferencesDataSource.setSelectedBusinessId(businessId)
    }

    override suspend fun setSelectedStoreId(storeId: UUID?) {
        userPreferencesDataSource.setSelectedStoreId(storeId)
    }

    override suspend fun setThemePreference(theme: ThemePreference) {
        userPreferencesDataSource.setThemePreference(theme)
    }

    override suspend fun setLanguagePreference(language: String) {
        userPreferencesDataSource.setLanguagePreference(language)
    }

    override suspend fun setOnboardingCompleted(completed: Boolean) {
        userPreferencesDataSource.setOnboardingCompleted(completed)
    }
}
