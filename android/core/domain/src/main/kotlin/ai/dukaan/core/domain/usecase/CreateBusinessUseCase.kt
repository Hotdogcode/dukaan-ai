package ai.dukaan.core.domain.usecase

import ai.dukaan.core.domain.repository.BusinessRepository
import ai.dukaan.core.model.BusinessMembership

class CreateBusinessUseCase(
    private val businessRepository: BusinessRepository,
) {
    suspend operator fun invoke(
        name: String,
        businessType: String = "GROCERY",
        ownerName: String? = null,
        language: String = "hi",
        initialStoreName: String? = null,
    ): Result<BusinessMembership> {
        return businessRepository.createBusiness(
            name = name,
            businessType = businessType,
            ownerName = ownerName,
            language = language,
            initialStoreName = initialStoreName,
        )
    }
}
