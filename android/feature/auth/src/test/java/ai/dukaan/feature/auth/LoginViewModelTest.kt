package ai.dukaan.feature.auth

import ai.dukaan.core.domain.usecase.RequestOtpUseCase
import ai.dukaan.core.testing.repository.FakeAuthRepository
import ai.dukaan.core.testing.rule.MainDispatcherRule
import ai.dukaan.feature.auth.login.LoginViewModel
import app.cash.turbine.test
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class LoginViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private lateinit var authRepository: FakeAuthRepository
    private lateinit var requestOtpUseCase: RequestOtpUseCase
    private lateinit var viewModel: LoginViewModel

    @Before
    fun setUp() {
        authRepository = FakeAuthRepository()
        requestOtpUseCase = RequestOtpUseCase(authRepository)
        viewModel = LoginViewModel(requestOtpUseCase)
    }

    @Test
    fun onPhoneNumberChanged_sanitizesAndLimitsTo10Digits() = runTest {
        viewModel.onPhoneNumberChanged("+91 98765-43210123")
        assertEquals("9876543210", viewModel.uiState.value.phoneNumber)
    }

    @Test
    fun requestOtp_invalidPhoneNumber_showsErrorMessage() = runTest {
        viewModel.onPhoneNumberChanged("12345")
        var successCalled = false
        viewModel.requestOtp { _, _ -> successCalled = true }

        assertFalse(successCalled)
        assertNotNull(viewModel.uiState.value.errorMessage)
    }

    @Test
    fun requestOtp_validPhoneNumber_invokesCallback() = runTest {
        viewModel.onPhoneNumberChanged("9876543210")
        var capturedPhone: String? = null
        var capturedRequestId: String? = null

        viewModel.requestOtp { phone, reqId ->
            capturedPhone = phone
            capturedRequestId = reqId
        }

        assertEquals("9876543210", capturedPhone)
        assertNotNull(capturedRequestId)
        assertTrue(viewModel.uiState.value.isOtpRequested)
    }

    @Test
    fun requestOtp_networkFailure_displaysError() = runTest {
        authRepository.shouldOtpRequestSucceed = false
        viewModel.onPhoneNumberChanged("9876543210")

        var successCalled = false
        viewModel.requestOtp { _, _ -> successCalled = true }

        assertFalse(successCalled)
        assertNotNull(viewModel.uiState.value.errorMessage)
    }
}
