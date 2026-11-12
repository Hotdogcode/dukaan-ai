package ai.dukaan.app.ui

import ai.dukaan.core.navigation.BusinessOnboardingRoute
import ai.dukaan.core.navigation.DashboardRoute
import ai.dukaan.core.navigation.LoginRoute
import ai.dukaan.core.navigation.OtpVerifyRoute
import ai.dukaan.core.navigation.SplashRoute
import ai.dukaan.feature.auth.login.LoginRoute
import ai.dukaan.feature.auth.otp.OtpVerifyRoute
import ai.dukaan.feature.auth.splash.SplashRoute
import ai.dukaan.feature.dashboard.DashboardRoute
import ai.dukaan.feature.onboarding.BusinessOnboardingRoute
import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.toRoute

@Composable
fun DukaanApp() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = SplashRoute,
    ) {
        composable<SplashRoute> {
            SplashRoute(
                onNavigateToLogin = {
                    navController.navigate(LoginRoute) {
                        popUpTo(SplashRoute) { inclusive = true }
                    }
                },
                onNavigateToOnboarding = {
                    navController.navigate(BusinessOnboardingRoute) {
                        popUpTo(SplashRoute) { inclusive = true }
                    }
                },
                onNavigateToDashboard = {
                    navController.navigate(DashboardRoute) {
                        popUpTo(SplashRoute) { inclusive = true }
                    }
                },
            )
        }

        composable<LoginRoute> {
            LoginRoute(
                onNavigateToOtp = { phoneNumber, requestId ->
                    navController.navigate(
                        OtpVerifyRoute(phoneNumber = phoneNumber, requestId = requestId)
                    )
                },
            )
        }

        composable<OtpVerifyRoute> { backStackEntry ->
            val route = backStackEntry.toRoute<OtpVerifyRoute>()
            OtpVerifyRoute(
                phoneNumber = route.phoneNumber,
                requestId = route.requestId,
                onNavigateToOnboarding = {
                    navController.navigate(BusinessOnboardingRoute) {
                        popUpTo(LoginRoute) { inclusive = true }
                    }
                },
                onNavigateToDashboard = {
                    navController.navigate(DashboardRoute) {
                        popUpTo(LoginRoute) { inclusive = true }
                    }
                },
            )
        }

        composable<BusinessOnboardingRoute> {
            BusinessOnboardingRoute(
                onNavigateToDashboard = {
                    navController.navigate(DashboardRoute) {
                        popUpTo(BusinessOnboardingRoute) { inclusive = true }
                    }
                },
            )
        }

        composable<DashboardRoute> {
            DashboardRoute()
        }
    }
}
