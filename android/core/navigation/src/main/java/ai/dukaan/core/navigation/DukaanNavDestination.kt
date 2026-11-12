package ai.dukaan.core.navigation

import kotlinx.serialization.Serializable

/**
 * Root sealed interface representing type-safe Navigation Compose routes in DukaanAI.
 */
sealed interface DukaanRoute

// Root Startup Destination
@Serializable
data object SplashRoute : DukaanRoute

// Authentication Navigation Graph Routes
@Serializable
data object AuthGraphRoute : DukaanRoute

@Serializable
data object LoginRoute : DukaanRoute

@Serializable
data class OtpVerifyRoute(
    val phoneNumber: String,
    val requestId: String? = null,
) : DukaanRoute

// Onboarding Navigation Graph Route
@Serializable
data object BusinessOnboardingRoute : DukaanRoute

// Main Application Navigation Graph Routes
@Serializable
data object MainGraphRoute : DukaanRoute

@Serializable
data object DashboardRoute : DukaanRoute

// Catalogue Navigation Graph Routes
@Serializable
data object ProductListRoute : DukaanRoute

@Serializable
data class ProductDetailsRoute(
    val productId: String,
) : DukaanRoute

@Serializable
data class AddProductRoute(
    val prefilledBarcode: String? = null,
) : DukaanRoute

@Serializable
data class EditProductRoute(
    val productId: String,
) : DukaanRoute

@Serializable
data object CategoryManagementRoute : DukaanRoute

@Serializable
data class BarcodeScannerRoute(
    val source: String = "SEARCH",
) : DukaanRoute
