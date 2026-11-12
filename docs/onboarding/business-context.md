# DukaanAI — Business Context & Multi-Tenant Authorization

## 1. Runtime Business Context
In DukaanAI, every authorized operation is executed within an explicit `BusinessContext`:

```kotlin
data class BusinessContext(
    val userId: UUID,
    val businessId: UUID,
    val storeId: UUID,
    val businessName: String,
    val storeName: String,
    val role: String,
    val permissions: Set<String> = emptySet(),
)
```

---

## 2. Request Interception & Multi-Tenancy Headers
All outgoing HTTP requests (via OkHttp `AuthInterceptor`) attach two mandatory headers:
1. `Authorization: Bearer <jwt_access_token>`: Identifies authenticated `User`.
2. `X-Business-ID: <uuid>`: Authoritatively scopes the request to the active tenant.

On the FastAPI backend, `require_permission(permission)` validates:
- Does the user hold an active `business_users` record for the specified `X-Business-ID`?
- Does the user's role contain the required permission (`business.read`, `business.update`, `inventory.manage`, etc.)?
- If either check fails, the request is rejected with HTTP 403 Forbidden (`BusinessAccessDenied` / `InsufficientPermissions`).

---

## 3. Offline Context Resilience
`UserPreferencesDataSource` caches the active `BusinessContext` in Jetpack DataStore:
- When the device is offline, `SplashViewModel` and `DashboardViewModel` retrieve the cached business and store IDs.
- Local Room database queries use the cached `businessId` to partition offline ledger records without data leakage.
