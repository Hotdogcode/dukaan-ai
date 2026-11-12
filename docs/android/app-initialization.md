# Application Initialization Architecture

## 1. Overview
The application initialization lifecycle is managed in the [`:app`](file:///c:/Dukan-AI/android/app) module through [`DukaanApplication`](file:///c:/Dukan-AI/android/app/src/main/java/ai/dukaan/app/DukaanApplication.kt). In accordance with architecture guidelines, the Application class contains **zero business logic**. Its sole responsibility is configuring essential framework engines and dependency injection graphs.

## 2. Initialization Components

### 2.1 Dependency Injection with Hilt
`DukaanApplication` is annotated with `@HiltAndroidApp`, triggering Hilt code generation and bootstrapping the `SingletonComponent` graph before any activity, service, or worker runs.

### 2.2 WorkManager Custom Configuration
To support dependency injection within background tasks via `@HiltWorker`, `DukaanApplication` implements `androidx.work.Configuration.Provider`:
```kotlin
@Inject
lateinit var workerFactory: HiltWorkerFactory

override val workManagerConfiguration: Configuration
    get() = Configuration.Builder()
        .setWorkerFactory(workerFactory)
        .build()
```
This enables constructor injection for background sync workers without requiring custom reflection or manual service locators.

### 2.3 Structured Logging Initialization
Logging is managed via **Timber**:
- In `DEBUG` builds, `Timber.plant(Timber.DebugTree())` is installed during `onCreate()`.
- In `RELEASE` builds, verbose debug trees are disabled, and logs are routed to crash analytics or security audit buffers.
- Sensitive values (passwords, OTPs, session tokens) are scrubbed before output.

## 3. Build Variants & Environment Configuration
DukaanAI defines two product flavors under the `environment` dimension:
- **`dev`** (`applicationIdSuffix = ".dev"`, `versionNameSuffix = "-dev"`):
  - Targets local or staging FastAPI backend: `http://10.0.2.2:8000/`.
  - Enables safe development HTTP logging.
  - Generates `DukaanAI Dev` app label.
- **`prod`**:
  - Targets production cloud backend: `https://api.dukaanai.app/`.
  - Enables R8 minification, resource shrinking, and code obfuscation.

Non-sensitive configuration is accessed via generated `BuildConfig` fields:
- `BuildConfig.BASE_URL`: Base API endpoint URL.
- `BuildConfig.ENVIRONMENT`: Current deployment stage string (`"development"` or `"production"`).
- `BuildConfig.API_VERSION`: API contract version (`"v1"`).
