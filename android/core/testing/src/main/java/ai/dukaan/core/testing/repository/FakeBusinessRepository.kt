package ai.dukaan.core.testing.repository

import ai.dukaan.core.domain.repository.BusinessRepository
import ai.dukaan.core.model.Business
import ai.dukaan.core.model.BusinessMembership
import java.util.UUID

class FakeBusinessRepository : BusinessRepository {

    private val businesses = mutableListOf<BusinessMembership>()
    var shouldFail: Boolean = false

    fun setBusinesses(list: List<BusinessMembership>) {
        businesses.clear()
        businesses.addAll(list)
    }

    override suspend fun getMyBusinesses(): Result<List<BusinessMembership>> {
        return if (!shouldFail) {
            Result.success(businesses.toList())
        } else {
            Result.failure(RuntimeException("Network failure fetching businesses"))
        }
    }

    override suspend fun createBusiness(
        name: String,
        businessType: String,
        ownerName: String?,
        language: String,
        initialStoreName: String?,
    ): Result<BusinessMembership> {
        return if (!shouldFail) {
            val biz = Business(
                id = UUID.randomUUID(),
                name = name,
                businessType = businessType,
                ownerName = ownerName,
                primaryLanguage = language,
            )
            val membership = BusinessMembership(
                business = biz,
                role = "OWNER",
                isActive = true,
                permissions = listOf("business.read", "business.update"),
            )
            businesses.add(membership)
            Result.success(membership)
        } else {
            Result.failure(RuntimeException("Failed to create business"))
        }
    }

    override suspend fun getBusiness(businessId: UUID): Result<Business> {
        val found = businesses.find { it.business.id == businessId }?.business
        return if (found != null) {
            Result.success(found)
        } else {
            Result.failure(RuntimeException("Business not found"))
        }
    }
}
