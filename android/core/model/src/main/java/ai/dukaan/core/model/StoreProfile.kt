package ai.dukaan.core.model

import java.util.UUID

/**
 * Basic store profile model representing a retail store instance.
 */
data class StoreProfile(
    val tenantId: UUID,
    val storeId: UUID,
    val storeName: String,
    val ownerName: String,
    val isOnline: Boolean = true,
)
