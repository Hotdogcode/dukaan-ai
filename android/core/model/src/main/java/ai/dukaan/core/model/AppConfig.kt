package ai.dukaan.core.model

import java.util.UUID

data class AppConfig(
    val selectedBusinessId: UUID? = null,
    val selectedStoreId: UUID? = null,
    val selectedBusinessName: String? = null,
    val selectedStoreName: String? = null,
    val userRole: String? = null,
    val userId: UUID? = null,
    val userPhoneNumber: String? = null,
    val userFullName: String? = null,
    val theme: ThemePreference = ThemePreference.SYSTEM,
    val language: String = "hi",
    val isOnboardingCompleted: Boolean = false,
)
