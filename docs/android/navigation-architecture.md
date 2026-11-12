# Navigation Architecture

## 1. Overview
DukaanAI leverages **Jetpack Navigation Compose 2.8+** with Kotlin Serialization type-safe routes. This eliminates brittle string URLs and manual bundle unpacking in favor of strongly-typed Kotlin objects and data classes.

All route definitions reside in the dedicated `:core:navigation` module, ensuring feature modules never reference each other directly for routing.

## 2. Type-Safe Route Definitions
In [`:core:navigation`](file:///c:/Dukan-AI/android/core/navigation/src/main/java/ai/dukaan/core/navigation/DukaanNavDestination.kt):

```kotlin
sealed interface DukaanRoute

// Root Destination
@Serializable
data object SplashRoute : DukaanRoute

// Authentication Graph
@Serializable
data object AuthGraphRoute : DukaanRoute

@Serializable
data object LoginRoute : DukaanRoute

@Serializable
data class OtpVerifyRoute(val phoneNumber: String) : DukaanRoute

// Onboarding Graph
@Serializable
data object BusinessOnboardingRoute : DukaanRoute

// Main App Graph
@Serializable
data object MainGraphRoute : DukaanRoute

@Serializable
data object DashboardRoute : DukaanRoute
```

## 3. Navigation Graph Separation
The top-level `NavHost` in `app/src/main/java/ai/dukaan/app/ui/DukaanApp.kt` separates user flows into distinct navigation subgraphs:

```
               +-------------------+
               |    SplashRoute    |
               +---------+---------+
                         |
           +-------------+-------------+
           | (Not authenticated)       | (Authenticated & Onboarded)
           v                           v
  +-----------------+         +-----------------+
  |   LoginRoute    |         | DashboardRoute  |
  +--------+--------+         +-----------------+
           |
           v
  +-----------------+
  | OtpVerifyRoute  |
  +--------+--------+
           |
           v
  +--------------------------+
  | BusinessOnboardingRoute  |
  +--------------------------+
```

### Deep-Link Readiness
Navigation Compose 2.8 automatically synthesizes deep-link patterns from `@Serializable` routes. Parameters (e.g. `phoneNumber` in `OtpVerifyRoute` or future `orderId` in receipt routes) can be bound to external URI intents (e.g. `dukaanai://auth/verify?phoneNumber=9876543210`).

## 4. How to Add a New Navigation Destination
1. **Define Route in `:core:navigation`**:
   ```kotlin
   @Serializable
   data class ProductDetailRoute(val productId: String) : DukaanRoute
   ```
2. **Implement Screen in Feature Module**:
   Accept callback lambdas for external navigation rather than accepting `NavController`:
   ```kotlin
   @Composable
   fun ProductDetailRoute(
       productId: String,
       onNavigateBack: () -> Unit,
   ) { ... }
   ```
3. **Register Destination in `DukaanApp.kt`**:
   ```kotlin
   composable<ProductDetailRoute> { backStackEntry ->
       val route = backStackEntry.toRoute<ProductDetailRoute>()
       ProductDetailRoute(
           productId = route.productId,
           onNavigateBack = { navController.popBackStack() },
       )
   }
   ```
