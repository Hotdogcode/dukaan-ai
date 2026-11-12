package ai.dukaan.core.domain.repository

import ai.dukaan.core.model.Business
import ai.dukaan.core.model.BusinessMembership
import java.util.UUID

/**
 * Domain repository contract for tenant businesses and staff membership.
 */
interface BusinessRepository {
    suspend fun getMyBusinesses(): Result<List<BusinessMembership>>
    suspend fun createBusiness(
        name: String,
        businessType: String = "GROCERY",
        ownerName: String? = null,
        language: String = "hi",
        initialStoreName: String? = null,
    ): Result<BusinessMembership>
    suspend fun getBusiness(businessId: UUID): Result<Business>
}
