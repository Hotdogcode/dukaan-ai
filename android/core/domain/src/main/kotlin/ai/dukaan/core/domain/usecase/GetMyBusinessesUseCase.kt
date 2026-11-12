package ai.dukaan.core.domain.usecase

import ai.dukaan.core.domain.repository.BusinessRepository
import ai.dukaan.core.model.BusinessMembership

class GetMyBusinessesUseCase(
    private val businessRepository: BusinessRepository,
) {
    suspend operator fun invoke(): Result<List<BusinessMembership>> {
        return businessRepository.getMyBusinesses()
    }
}
