package ai.dukaan.feature.auth

import ai.dukaan.core.domain.usecase.GetMyBusinessesUseCase
import ai.dukaan.core.domain.usecase.RequestOtpUseCase
import ai.dukaan.core.domain.usecase.VerifyOtpUseCase
import ai.dukaan.core.model.Business
import ai.dukaan.core.model.BusinessMembership
import ai.dukaan.core.testing.repository.FakeAuthRepository
import ai.dukaan.core.testing.repository.FakeBusinessRepository
import ai.dukaan.core.testing.rule.MainDispatcherRule
import ai.dukaan.feature.auth.otp.OtpVerifyViewModel
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import java.util.UUID

class OtpVerifyViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private lateinit var authRepository: FakeAuthRepository
    private lateinit var businessRepository: FakeBusinessRepository
    private lateinit var verifyOtpUseCase: VerifyOtpUseCase
    private lateinit var requestOtpUseCase: RequestOtpUseCase
    private lateinit var getMyBusinessesUseCase: GetMyBusinessesUseCase
    private lateinit var viewModel: OtpVerifyViewModel

    @Before
    fun setUp() {
        authRepository = FakeAuthRepository()
        businessRepository = FakeBusinessRepository()
        verifyOtpUseCase = VerifyOtpUseCase(authRepository)
        requestOtpUseCase = RequestOtpUseCase(authRepository)
        getMyBusinessesUseCase = GetMyBusinessesUseCase(businessRepository)

        viewModel = OtpVerifyViewModel(
            verifyOtpUseCase = verifyOtpUseCase,
            requestOtpUseCase = requestOtpUseCase,
            getMyBusinessesUseCase = getMyBusinessesUseCase,
        )
        viewModel.initialize("9876543210", "fake-req-id")
    }

    @Test
    fun onOtpCodeChanged_sanitizesTo6Digits() = runTest {
        viewModel.onOtpCodeChanged("12a34b5678")
        assertEquals("123456", viewModel.uiState.value.otpCode)
    }

    @Test
    fun verifyOtp_shortCode_showsError() = runTest {
        viewModel.onOtpCodeChanged("1234")
        var onboardingCalled = false
        var dashboardCalled = false

        viewModel.verifyOtp(
            onNavigateToOnboarding = { onboardingCalled = true },
            onNavigateToDashboard = { dashboardCalled = true },
        )

        assertFalse(onboardingCalled)
        assertFalse(dashboardCalled)
        assertNotNull(viewModel.uiState.value.errorMessage)
    }

    @Test
    fun verifyOtp_successNoBusinesses_routesToOnboarding() = runTest {
        viewModel.onOtpCodeChanged("123456")
        businessRepository.setBusinesses(emptyList())

        var onboardingCalled = false
        var dashboardCalled = false

        viewModel.verifyOtp(
            onNavigateToOnboarding = { onboardingCalled = true },
            onNavigateToDashboard = { dashboardCalled = true },
        )

        assertTrue(onboardingCalled)
        assertFalse(dashboardCalled)
    }

    @Test
    fun verifyOtp_successWithBusiness_routesToDashboard() = runTest {
        viewModel.onOtpCodeChanged("123456")
        val biz = Business(id = UUID.randomUUID(), name = "Gupta Store")
        businessRepository.setBusinesses(
            listOf(
                BusinessMembership(
                    business = biz,
                    role = "OWNER",
                    isActive = true,
                    permissions = listOf("business.read"),
                )
            )
        )

        var onboardingCalled = false
        var dashboardCalled = false

        viewModel.verifyOtp(
            onNavigateToOnboarding = { onboardingCalled = true },
            onNavigateToDashboard = { dashboardCalled = true },
        )

        assertFalse(onboardingCalled)
        assertTrue(dashboardCalled)
    }

    @Test
    fun verifyOtp_failure_displaysError() = runTest {
        authRepository.shouldVerifySucceed = false
        viewModel.onOtpCodeChanged("123456")

        var onboardingCalled = false
        var dashboardCalled = false

        viewModel.verifyOtp(
            onNavigateToOnboarding = { onboardingCalled = true },
            onNavigateToDashboard = { dashboardCalled = true },
        )

        assertFalse(onboardingCalled)
        assertFalse(dashboardCalled)
        assertNotNull(viewModel.uiState.value.errorMessage)
    }
}
