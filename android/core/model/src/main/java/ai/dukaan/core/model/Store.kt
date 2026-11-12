package ai.dukaan.core.model

import java.util.UUID

/**
 * Physical retail store outlet owned by a Business tenant.
 */
data class Store(
    val id: UUID,
    val businessId: UUID,
    val name: String,
    val code: String? = null,
    val addressLine1: String,
    val addressLine2: String? = null,
    val city: String,
    val state: String,
    val pincode: String,
    val phoneNumber: String? = null,
    val isPrimary: Boolean = false,
    val timezone: String = "Asia/Kolkata",
    val isActive: Boolean = true,
)
