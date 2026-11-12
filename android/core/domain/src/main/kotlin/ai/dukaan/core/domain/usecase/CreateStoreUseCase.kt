package ai.dukaan.core.domain.usecase

import ai.dukaan.core.domain.repository.StoreRepository
import ai.dukaan.core.model.Store
import java.util.UUID

class CreateStoreUseCase(
    private val storeRepository: StoreRepository,
) {
    suspend operator fun invoke(
        businessId: UUID,
        name: String,
        code: String? = null,
        addressLine1: String,
        city: String,
        state: String,
        pincode: String,
        isPrimary: Boolean = false,
    ): Result<Store> {
        return storeRepository.createStore(
            businessId = businessId,
            name = name,
            code = code,
            addressLine1 = addressLine1,
            city = city,
            state = state,
            pincode = pincode,
            isPrimary = isPrimary,
        )
    }
}
