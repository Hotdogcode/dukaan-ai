package ai.dukaan.feature.auth

import ai.dukaan.core.domain.usecase.GetAppConfigUseCase
import ai.dukaan.core.model.Business
import ai.dukaan.core.model.BusinessMembership
import ai.dukaan.core.testing.repository.FakeAppConfigRepository
import ai.dukaan.core.testing.repository.FakeAuthRepository
import ai.dukaan.core.testing.repository.FakeBusinessRepository
import ai.dukaan.core.testing.rule.MainDispatcherRule
import ai.dukaan.feature.auth.splash.SplashTarget
import ai.dukaan.feature.auth.splash.SplashUiState
import ai.dukaan.feature.auth.splash.SplashViewModel
import app.cash.turbine.test
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import java.util.UUID

class SplashViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private lateinit var appConfigRepository: FakeAppConfigRepository
    private lateinit var authRepository: FakeAuthRepository
    private lateinit var businessRepository: FakeBusinessRepository
    private lateinit var getAppConfigUseCase: GetAppConfigUseCase
    private lateinit var viewModel: SplashViewModel

    @Before
    fun setUp() {
        appConfigRepository = FakeAppConfigRepository()
        authRepository = FakeAuthRepository()
        businessRepository = FakeBusinessRepository()
        getAppConfigUseCase = GetAppConfigUseCase(appConfigRepository)
    }

    @Test
    fun unauthenticatedUser_withoutRefreshToken_routesToLogin() = runTest {
        authRepository.setAuthenticated(false)
        authRepository.shouldRefreshSucceed = false

        viewModel = SplashViewModel(
            getAppConfigUseCase = getAppConfigUseCase,
            authRepository = authRepository,
            businessRepository = businessRepository,
        )

        viewModel.uiState.test {
            val item = awaitItem()
            if (item is SplashUiState.Loading) {
                val next = awaitItem()
                assertEquals(SplashUiState.Success(SplashTarget.LOGIN), next)
            } else {
                assertEquals(SplashUiState.Success(SplashTarget.LOGIN), item)
            }
        }
    }

    @Test
    fun authenticatedUser_withoutBusinesses_routesToOnboarding() = runTest {
        authRepository.setAuthenticated(true)
        businessRepository.setBusinesses(emptyList())

        viewModel = SplashViewModel(
            getAppConfigUseCase = getAppConfigUseCase,
            authRepository = authRepository,
            businessRepository = businessRepository,
        )

        viewModel.uiState.test {
            val item = awaitItem()
            if (item is SplashUiState.Loading) {
                val next = awaitItem()
                assertEquals(SplashUiState.Success(SplashTarget.ONBOARDING), next)
            } else {
                assertEquals(SplashUiState.Success(SplashTarget.ONBOARDING), item)
            }
        }
    }

    @Test
    fun authenticatedUser_withExistingBusiness_routesToDashboard() = runTest {
        authRepository.setAuthenticated(true)
        val biz = Business(
            id = UUID.randomUUID(),
            name = "Ramesh Kirana",
        )
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

        viewModel = SplashViewModel(
            getAppConfigUseCase = getAppConfigUseCase,
            authRepository = authRepository,
            businessRepository = businessRepository,
        )

        viewModel.uiState.test {
            val item = awaitItem()
            if (item is SplashUiState.Loading) {
                val next = awaitItem()
                assertEquals(SplashUiState.Success(SplashTarget.DASHBOARD), next)
            } else {
                assertEquals(SplashUiState.Success(SplashTarget.DASHBOARD), item)
            }
        }
    }
}
