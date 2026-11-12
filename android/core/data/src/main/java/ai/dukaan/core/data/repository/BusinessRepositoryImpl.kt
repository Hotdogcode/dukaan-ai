package ai.dukaan.core.data.repository

import ai.dukaan.core.datastore.UserPreferencesDataSource
import ai.dukaan.core.domain.repository.BusinessRepository
import ai.dukaan.core.model.Business
import ai.dukaan.core.model.BusinessMembership
import ai.dukaan.core.network.api.BusinessApiService
import ai.dukaan.core.network.model.BusinessCreateNetwork
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BusinessRepositoryImpl @Inject constructor(
    private val businessApiService: BusinessApiService,
    private val userPreferencesDataSource: UserPreferencesDataSource,
) : BusinessRepository {

    override suspend fun getMyBusinesses(): Result<List<BusinessMembership>> = runCatching {
        val response = businessApiService.listMyBusinesses()
        if (!response.isSuccessful) {
            val error = response.errorBody()?.string()
            throw RuntimeException("Failed to fetch businesses: HTTP ${response.code()} $error")
        }
        val list = response.body() ?: emptyList()
        list.map { item ->
            val b = item.business
            BusinessMembership(
                business = Business(
                    id = UUID.fromString(b.id),
                    name = b.name,
                    businessType = b.businessType,
                    ownerName = b.ownerName,
                    legalName = b.legalName,
                    gstin = b.gstin,
                    currency = b.currency,
                    timezone = b.timezone,
                    primaryLanguage = b.primaryLanguage,
                    isActive = b.isActive,
                ),
                role = item.role,
                isActive = item.isActive,
                permissions = item.permissions,
            )
        }
    }

    override suspend fun createBusiness(
        name: String,
        businessType: String,
        ownerName: String?,
        language: String,
        initialStoreName: String?,
    ): Result<BusinessMembership> = runCatching {
        val payload = BusinessCreateNetwork(
            name = name,
            businessType = businessType,
            ownerName = ownerName,
            primaryLanguage = language,
            initialStoreName = initialStoreName,
        )
        val response = businessApiService.createBusiness(payload)
        if (!response.isSuccessful) {
            val error = response.errorBody()?.string()
            throw RuntimeException("Failed to create business: HTTP ${response.code()} $error")
        }
        val body = response.body() ?: throw RuntimeException("Empty response body from business creation")
        val b = body.business
        val businessId = UUID.fromString(b.id)

        // Save active business context in DataStore
        userPreferencesDataSource.setBusinessContext(
            businessId = businessId,
            storeId = null,
            businessName = b.name,
            storeName = initialStoreName ?: "${b.name} Main Store",
            role = body.role,
        )
        userPreferencesDataSource.setOnboardingCompleted(true)

        BusinessMembership(
            business = Business(
                id = businessId,
                name = b.name,
                businessType = b.businessType,
                ownerName = b.ownerName,
                legalName = b.legalName,
                gstin = b.gstin,
                currency = b.currency,
                timezone = b.timezone,
                primaryLanguage = b.primaryLanguage,
                isActive = b.isActive,
            ),
            role = body.role,
            isActive = body.isActive,
            permissions = body.permissions,
        )
    }

    override suspend fun getBusiness(businessId: UUID): Result<Business> = runCatching {
        val response = businessApiService.getBusiness(businessId.toString())
        if (!response.isSuccessful) {
            val error = response.errorBody()?.string()
            throw RuntimeException("Failed to get business: HTTP ${response.code()} $error")
        }
        val b = response.body() ?: throw RuntimeException("Empty response from get business")
        Business(
            id = UUID.fromString(b.id),
            name = b.name,
            businessType = b.businessType,
            ownerName = b.ownerName,
            legalName = b.legalName,
            gstin = b.gstin,
            currency = b.currency,
            timezone = b.timezone,
            primaryLanguage = b.primaryLanguage,
            isActive = b.isActive,
        )
    }
}
