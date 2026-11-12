package ai.dukaan.feature.onboarding

import ai.dukaan.core.domain.usecase.CreateBusinessUseCase
import ai.dukaan.core.testing.repository.FakeBusinessRepository
import ai.dukaan.core.testing.rule.MainDispatcherRule
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class BusinessOnboardingViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private lateinit var businessRepository: FakeBusinessRepository
    private lateinit var createBusinessUseCase: CreateBusinessUseCase
    private lateinit var viewModel: BusinessOnboardingViewModel

    @Before
    fun setUp() {
        businessRepository = FakeBusinessRepository()
        createBusinessUseCase = CreateBusinessUseCase(businessRepository)
        viewModel = BusinessOnboardingViewModel(createBusinessUseCase)
    }

    @Test
    fun submitOnboarding_emptyName_showsError() = runTest {
        viewModel.onBusinessNameChanged(" ")
        var successCalled = false

        viewModel.submitOnboarding { successCalled = true }

        assertFalse(successCalled)
        assertNotNull(viewModel.uiState.value.errorMessage)
    }

    @Test
    fun submitOnboarding_validData_succeedsAndNavigates() = runTest {
        viewModel.onBusinessNameChanged("Maa Sharda Kirana")
        viewModel.onOwnerNameChanged("Suresh Sharma")
        viewModel.onCityChanged("Indore")
        viewModel.onPincodeChanged("452001")

        var successCalled = false
        viewModel.submitOnboarding { successCalled = true }

        assertTrue(successCalled)
    }

    @Test
    fun submitOnboarding_backendFailure_showsError() = runTest {
        businessRepository.shouldFail = true
        viewModel.onBusinessNameChanged("Maa Sharda Kirana")

        var successCalled = false
        viewModel.submitOnboarding { successCalled = true }

        assertFalse(successCalled)
        assertNotNull(viewModel.uiState.value.errorMessage)
    }
}
