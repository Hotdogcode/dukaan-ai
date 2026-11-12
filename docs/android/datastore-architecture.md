# DataStore Preferences Architecture

## 1. Overview
Application preferences, active store selection, and user experience configurations are persisted in [`:core:datastore`](file:///c:/Dukan-AI/android/core/datastore) using **Jetpack DataStore Preferences**. DataStore replaces legacy `SharedPreferences`, providing asynchronous, transactional, and type-safe data storage backed by Kotlin Coroutines and Flow.

## 2. Managed Preferences (`UserPreferencesDataSource`)
[`UserPreferencesDataSource`](file:///c:/Dukan-AI/android/core/datastore/src/main/java/ai/dukaan/core/datastore/UserPreferencesDataSource.kt) manages the following typed parameters:

| Preference Key | Type | Description |
| :--- | :--- | :--- |
| `selected_business_id` | `UUID?` | Active business tenant UUID for multi-store kirana accounts. |
| `selected_store_id` | `UUID?` | Active retail branch/store UUID. |
| `theme_preference` | `ThemePreference` | `SYSTEM`, `LIGHT`, or `DARK`. |
| `language_preference` | `String` | Preferred UI locale (e.g. `"en"` for English, `"hi"` for Hindi). |
| `is_onboarding_completed` | `Boolean` | Flag indicating whether the shop owner has finished initial store setup. |

### Reactive Emission
Preferences are exposed to domain use cases as a unified, immutable reactive stream:
```kotlin
val appConfig: Flow<AppConfig>
```
When a shop owner toggles dark mode or switches between stores, the new configuration immediately propagates to all observing Composables via `collectAsStateWithLifecycle()`.

## 3. Secure Token Storage Strategy (Authentication Isolation)
In strict accordance with security constraints:
- **Authentication tokens (JWT access tokens, refresh tokens, PIN hashes) are NEVER stored in ordinary DataStore or plaintext SharedPreferences.**
- In Stage 06+, authentication credentials will be stored using **Android Keystore-backed encrypted storage** (`EncryptedSharedPreferences` / Jetpack Security Crypto) using AES-256 GCM encryption.
- This ensures tokens cannot be extracted from rooted devices, unencrypted backups, or memory dumps.
