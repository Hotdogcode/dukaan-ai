package ai.dukaan.core.domain.repository

import ai.dukaan.core.model.Store
import java.util.UUID

/**
 * Domain repository contract for physical store outlets.
 */
interface StoreRepository {
    suspend fun getStores(businessId: UUID): Result<List<Store>>
    suspend fun createStore(
        businessId: UUID,
        name: String,
        code: String? = null,
        addressLine1: String,
        city: String,
        state: String,
        pincode: String,
        isPrimary: Boolean = false,
    ): Result<Store>
    suspend fun getStore(businessId: UUID, storeId: UUID): Result<Store>
}
