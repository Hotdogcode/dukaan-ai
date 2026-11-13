package ai.dukaan.app.ui

import ai.dukaan.core.navigation.AddProductRoute
import ai.dukaan.core.navigation.BarcodeScannerRoute
import ai.dukaan.core.navigation.BusinessOnboardingRoute
import ai.dukaan.core.navigation.CategoryManagementRoute
import ai.dukaan.core.navigation.DashboardRoute
import ai.dukaan.core.navigation.EditProductRoute
import ai.dukaan.core.navigation.InventoryDashboardRoute
import ai.dukaan.core.navigation.InventoryListRoute
import ai.dukaan.core.navigation.LoginRoute
import ai.dukaan.core.navigation.OpeningStockRoute
import ai.dukaan.core.navigation.OtpVerifyRoute
import ai.dukaan.core.navigation.ProductDetailsRoute
import ai.dukaan.core.navigation.ProductListRoute
import ai.dukaan.core.navigation.SplashRoute
import ai.dukaan.core.navigation.StockAdjustmentRoute
import ai.dukaan.core.navigation.StockCountRoute
import ai.dukaan.core.navigation.StockDetailsRoute
import ai.dukaan.feature.auth.login.LoginRoute
import ai.dukaan.feature.auth.otp.OtpVerifyRoute
import ai.dukaan.feature.auth.splash.SplashRoute
import ai.dukaan.feature.catalogue.AddEditProductScreen
import ai.dukaan.feature.catalogue.BarcodeScannerScreen
import ai.dukaan.feature.catalogue.CategoryManagementScreen
import ai.dukaan.feature.catalogue.ProductDetailsScreen
import ai.dukaan.feature.catalogue.ProductListScreen
import ai.dukaan.feature.dashboard.DashboardRoute
import ai.dukaan.feature.inventory.InventoryDashboardScreen
import ai.dukaan.feature.inventory.InventoryListScreen
import ai.dukaan.feature.inventory.OpeningStockScreen
import ai.dukaan.feature.inventory.StockAdjustmentScreen
import ai.dukaan.feature.inventory.StockCountScreen
import ai.dukaan.feature.inventory.StockDetailsScreen
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
            DashboardRoute(
                onNavigateToCatalogue = {
                    navController.navigate(ProductListRoute)
                },
                onNavigateToInventory = {
                    navController.navigate(InventoryDashboardRoute)
                },
            )
        }

        // -----------------------------------------------------------------
        // Product Catalogue Navigation Routes (Stage 07)
        // -----------------------------------------------------------------
        composable<ProductListRoute> {
            ProductListScreen(
                onNavigateToAddProduct = {
                    navController.navigate(AddProductRoute())
                },
                onNavigateToProductDetails = { productId ->
                    navController.navigate(ProductDetailsRoute(productId = productId))
                },
                onNavigateToBarcodeScanner = {
                    navController.navigate(BarcodeScannerRoute(source = "SEARCH"))
                },
                onNavigateToCategoryManagement = {
                    navController.navigate(CategoryManagementRoute)
                },
            )
        }

        composable<AddProductRoute> {
            AddEditProductScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToScanBarcode = {
                    navController.navigate(BarcodeScannerRoute(source = "ADD_PRODUCT"))
                },
            )
        }

        composable<EditProductRoute> {
            AddEditProductScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToScanBarcode = {
                    navController.navigate(BarcodeScannerRoute(source = "ADD_PRODUCT"))
                },
            )
        }

        composable<ProductDetailsRoute> {
            ProductDetailsScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToEdit = { productId ->
                    navController.navigate(EditProductRoute(productId = productId))
                },
            )
        }

        composable<CategoryManagementRoute> {
            CategoryManagementScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
            )
        }

        composable<BarcodeScannerRoute> { backStackEntry ->
            val route = backStackEntry.toRoute<BarcodeScannerRoute>()
            BarcodeScannerScreen(
                onBarcodeScanned = { scannedCode ->
                    if (route.source == "ADD_PRODUCT") {
                        navController.popBackStack()
                        navController.navigate(AddProductRoute(prefilledBarcode = scannedCode))
                    } else {
                        // In search mode, pop and open AddProduct with prefill or filter
                        navController.popBackStack()
                        navController.navigate(AddProductRoute(prefilledBarcode = scannedCode))
                    }
                },
                onNavigateBack = {
                    navController.popBackStack()
                },
            )
        }

        // -----------------------------------------------------------------
        // Inventory & Stock Ledger Navigation Routes (Stage 08)
        // -----------------------------------------------------------------
        composable<InventoryDashboardRoute> {
            InventoryDashboardScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToList = {
                    navController.navigate(InventoryListRoute)
                },
                onNavigateToOpeningStock = {
                    navController.navigate(OpeningStockRoute())
                },
                onNavigateToAdjustment = {
                    navController.navigate(StockAdjustmentRoute())
                },
                onNavigateToStockCount = {
                    navController.navigate(StockCountRoute)
                },
            )
        }

        composable<InventoryListRoute> {
            InventoryListScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToDetails = { variantId ->
                    navController.navigate(StockDetailsRoute(variantId = variantId.toString()))
                },
                onNavigateToAdjustment = {
                    navController.navigate(StockAdjustmentRoute())
                },
            )
        }

        composable<StockDetailsRoute> {
            StockDetailsScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToAdjustment = { variantId ->
                    navController.navigate(StockAdjustmentRoute(variantId = variantId))
                },
                onNavigateToOpeningStock = { variantId ->
                    navController.navigate(OpeningStockRoute(variantId = variantId))
                },
            )
        }

        composable<OpeningStockRoute> {
            OpeningStockScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
            )
        }

        composable<StockAdjustmentRoute> {
            StockAdjustmentScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
            )
        }

        composable<StockCountRoute> {
            StockCountScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
            )
        }
    }
}
