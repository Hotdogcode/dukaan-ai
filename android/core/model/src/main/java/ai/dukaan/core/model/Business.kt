package ai.dukaan.core.model

import java.util.UUID

/**
 * Tenant business entity.
 */
data class Business(
    val id: UUID,
    val name: String,
    val businessType: String? = null,
    val ownerName: String? = null,
    val legalName: String? = null,
    val gstin: String? = null,
    val currency: String = "INR",
    val timezone: String = "Asia/Kolkata",
    val primaryLanguage: String = "hi",
    val isActive: Boolean = true,
)

/**
 * User membership association with role and granted permissions.
 */
data class BusinessMembership(
    val business: Business,
    val role: String,
    val isActive: Boolean,
    val permissions: List<String>,
)
