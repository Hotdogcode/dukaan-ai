package ai.dukaan.core.data.repository

import ai.dukaan.core.domain.repository.StoreRepository
import ai.dukaan.core.model.Store
import ai.dukaan.core.network.api.StoreApiService
import ai.dukaan.core.network.model.StoreCreateNetwork
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class StoreRepositoryImpl @Inject constructor(
    private val storeApiService: StoreApiService,
) : StoreRepository {

    override suspend fun getStores(businessId: UUID): Result<List<Store>> = runCatching {
        val response = storeApiService.listStores(businessId.toString())
        if (!response.isSuccessful) {
            val error = response.errorBody()?.string()
            throw RuntimeException("Failed to fetch stores: HTTP ${response.code()} $error")
        }
        val list = response.body() ?: emptyList()
        list.map { s ->
            Store(
                id = UUID.fromString(s.id),
                businessId = UUID.fromString(s.businessId),
                name = s.name,
                code = s.code,
                addressLine1 = s.addressLine1,
                addressLine2 = s.addressLine2,
                city = s.city,
                state = s.state,
                pincode = s.pincode,
                phoneNumber = s.phoneNumber,
                isPrimary = s.isPrimary,
                timezone = s.timezone,
                isActive = s.isActive,
            )
        }
    }

    override suspend fun createStore(
        businessId: UUID,
        name: String,
        code: String?,
        addressLine1: String,
        city: String,
        state: String,
        pincode: String,
        isPrimary: Boolean,
    ): Result<Store> = runCatching {
        val payload = StoreCreateNetwork(
            name = name,
            code = code,
            addressLine1 = addressLine1,
            city = city,
            state = state,
            pincode = pincode,
            isPrimary = isPrimary,
        )
        val response = storeApiService.createStore(businessId.toString(), payload)
        if (!response.isSuccessful) {
            val error = response.errorBody()?.string()
            throw RuntimeException("Failed to create store: HTTP ${response.code()} $error")
        }
        val s = response.body() ?: throw RuntimeException("Empty response body from create store")
        Store(
            id = UUID.fromString(s.id),
            businessId = UUID.fromString(s.businessId),
            name = s.name,
            code = s.code,
            addressLine1 = s.addressLine1,
            addressLine2 = s.addressLine2,
            city = s.city,
            state = s.state,
            pincode = s.pincode,
            phoneNumber = s.phoneNumber,
            isPrimary = s.isPrimary,
            timezone = s.timezone,
            isActive = s.isActive,
        )
    }

    override suspend fun getStore(businessId: UUID, storeId: UUID): Result<Store> = runCatching {
        val response = storeApiService.getStore(businessId.toString(), storeId.toString())
        if (!response.isSuccessful) {
            val error = response.errorBody()?.string()
            throw RuntimeException("Failed to get store: HTTP ${response.code()} $error")
        }
        val s = response.body() ?: throw RuntimeException("Empty response body from get store")
        Store(
            id = UUID.fromString(s.id),
            businessId = UUID.fromString(s.businessId),
            name = s.name,
            code = s.code,
            addressLine1 = s.addressLine1,
            addressLine2 = s.addressLine2,
            city = s.city,
            state = s.state,
            pincode = s.pincode,
            phoneNumber = s.phoneNumber,
            isPrimary = s.isPrimary,
            timezone = s.timezone,
            isActive = s.isActive,
        )
    }
}
