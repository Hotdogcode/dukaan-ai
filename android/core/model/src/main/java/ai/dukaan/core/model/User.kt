package ai.dukaan.core.model

import java.util.UUID

/**
 * Verified user entity in DukaanAI.
 */
data class User(
    val id: UUID,
    val phoneNumber: String,
    val fullName: String?,
    val isActive: Boolean = true,
)
