package ai.dukaan.core.datastore

import ai.dukaan.core.model.AppConfig
import ai.dukaan.core.model.ThemePreference
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.emptyPreferences
import androidx.datastore.preferences.core.stringPreferencesKey
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.map
import java.io.IOException
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class UserPreferencesDataSource @Inject constructor(
    private val dataStore: DataStore<Preferences>,
) {
    val appConfig: Flow<AppConfig> = dataStore.data
        .catch { exception ->
            if (exception is IOException) {
                emit(emptyPreferences())
            } else {
                throw exception
            }
        }
        .map { preferences ->
            val businessId = preferences[KEY_BUSINESS_ID]?.let { runCatching { UUID.fromString(it) }.getOrNull() }
            val storeId = preferences[KEY_STORE_ID]?.let { runCatching { UUID.fromString(it) }.getOrNull() }
            val businessName = preferences[KEY_BUSINESS_NAME]
            val storeName = preferences[KEY_STORE_NAME]
            val userRole = preferences[KEY_USER_ROLE]
            val userId = preferences[KEY_USER_ID]?.let { runCatching { UUID.fromString(it) }.getOrNull() }
            val phoneNumber = preferences[KEY_USER_PHONE]
            val fullName = preferences[KEY_USER_NAME]
            val theme = preferences[KEY_THEME]?.let { runCatching { ThemePreference.valueOf(it) }.getOrNull() } ?: ThemePreference.SYSTEM
            val language = preferences[KEY_LANGUAGE] ?: "hi"
            val onboardingCompleted = preferences[KEY_ONBOARDING_COMPLETED] ?: false

            AppConfig(
                selectedBusinessId = businessId,
                selectedStoreId = storeId,
                selectedBusinessName = businessName,
                selectedStoreName = storeName,
                userRole = userRole,
                userId = userId,
                userPhoneNumber = phoneNumber,
                userFullName = fullName,
                theme = theme,
                language = language,
                isOnboardingCompleted = onboardingCompleted,
            )
        }

    suspend fun setSelectedBusinessId(businessId: UUID?) {
        dataStore.edit { preferences ->
            if (businessId == null) {
                preferences.remove(KEY_BUSINESS_ID)
            } else {
                preferences[KEY_BUSINESS_ID] = businessId.toString()
            }
        }
    }

    suspend fun setSelectedStoreId(storeId: UUID?) {
        dataStore.edit { preferences ->
            if (storeId == null) {
                preferences.remove(KEY_STORE_ID)
            } else {
                preferences[KEY_STORE_ID] = storeId.toString()
            }
        }
    }

    suspend fun setBusinessContext(
        businessId: UUID?,
        storeId: UUID?,
        businessName: String?,
        storeName: String?,
        role: String?,
    ) {
        dataStore.edit { preferences ->
            if (businessId == null) preferences.remove(KEY_BUSINESS_ID) else preferences[KEY_BUSINESS_ID] = businessId.toString()
            if (storeId == null) preferences.remove(KEY_STORE_ID) else preferences[KEY_STORE_ID] = storeId.toString()
            if (businessName == null) preferences.remove(KEY_BUSINESS_NAME) else preferences[KEY_BUSINESS_NAME] = businessName
            if (storeName == null) preferences.remove(KEY_STORE_NAME) else preferences[KEY_STORE_NAME] = storeName
            if (role == null) preferences.remove(KEY_USER_ROLE) else preferences[KEY_USER_ROLE] = role
        }
    }

    suspend fun setUserProfile(userId: UUID?, phoneNumber: String?, fullName: String?) {
        dataStore.edit { preferences ->
            if (userId == null) preferences.remove(KEY_USER_ID) else preferences[KEY_USER_ID] = userId.toString()
            if (phoneNumber == null) preferences.remove(KEY_USER_PHONE) else preferences[KEY_USER_PHONE] = phoneNumber
            if (fullName == null) preferences.remove(KEY_USER_NAME) else preferences[KEY_USER_NAME] = fullName
        }
    }

    suspend fun clearSession() {
        dataStore.edit { preferences ->
            preferences.remove(KEY_BUSINESS_ID)
            preferences.remove(KEY_STORE_ID)
            preferences.remove(KEY_BUSINESS_NAME)
            preferences.remove(KEY_STORE_NAME)
            preferences.remove(KEY_USER_ROLE)
            preferences.remove(KEY_USER_ID)
            preferences.remove(KEY_USER_PHONE)
            preferences.remove(KEY_USER_NAME)
            preferences.remove(KEY_ONBOARDING_COMPLETED)
        }
    }

    suspend fun setThemePreference(theme: ThemePreference) {
        dataStore.edit { preferences ->
            preferences[KEY_THEME] = theme.name
        }
    }

    suspend fun setLanguagePreference(language: String) {
        dataStore.edit { preferences ->
            preferences[KEY_LANGUAGE] = language
        }
    }

    suspend fun setOnboardingCompleted(completed: Boolean) {
        dataStore.edit { preferences ->
            preferences[KEY_ONBOARDING_COMPLETED] = completed
        }
    }

    companion object {
        private val KEY_BUSINESS_ID = stringPreferencesKey("selected_business_id")
        private val KEY_STORE_ID = stringPreferencesKey("selected_store_id")
        private val KEY_BUSINESS_NAME = stringPreferencesKey("selected_business_name")
        private val KEY_STORE_NAME = stringPreferencesKey("selected_store_name")
        private val KEY_USER_ROLE = stringPreferencesKey("user_role")
        private val KEY_USER_ID = stringPreferencesKey("user_id")
        private val KEY_USER_PHONE = stringPreferencesKey("user_phone")
        private val KEY_USER_NAME = stringPreferencesKey("user_name")
        private val KEY_THEME = stringPreferencesKey("theme_preference")
        private val KEY_LANGUAGE = stringPreferencesKey("language_preference")
        private val KEY_ONBOARDING_COMPLETED = booleanPreferencesKey("is_onboarding_completed")
    }
}
