package ai.dukaan.core.domain.usecase

import ai.dukaan.core.domain.repository.StoreRepository
import ai.dukaan.core.model.Store
import java.util.UUID

class GetStoresUseCase(
    private val storeRepository: StoreRepository,
) {
    suspend operator fun invoke(businessId: UUID): Result<List<Store>> {
        return storeRepository.getStores(businessId)
    }
}
