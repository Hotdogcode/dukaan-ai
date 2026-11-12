package ai.dukaan.core.domain.repository

import ai.dukaan.core.model.AppConfig
import ai.dukaan.core.model.ThemePreference
import kotlinx.coroutines.flow.Flow
import java.util.UUID

interface AppConfigRepository {
    val appConfig: Flow<AppConfig>
    suspend fun setSelectedBusinessId(businessId: UUID?)
    suspend fun setSelectedStoreId(storeId: UUID?)
    suspend fun setThemePreference(theme: ThemePreference)
    suspend fun setLanguagePreference(language: String)
    suspend fun setOnboardingCompleted(completed: Boolean)
}
