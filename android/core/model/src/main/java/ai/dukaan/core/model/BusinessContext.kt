package ai.dukaan.core.model

import java.util.UUID

/**
 * Active runtime tenant and store scope for the authenticated user session.
 */
data class BusinessContext(
    val userId: UUID,
    val businessId: UUID,
    val storeId: UUID,
    val businessName: String,
    val storeName: String,
    val role: String,
    val permissions: Set<String> = emptySet(),
)
