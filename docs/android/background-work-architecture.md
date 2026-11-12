# Background Work Architecture (WorkManager)

## 1. Overview
Background synchronization, transaction journal flushing, and catalog backups in DukaanAI are powered by **Jetpack WorkManager**. WorkManager provides guaranteed, battery-conscious, and constraint-aware task execution that survives process death and device reboots.

## 2. Infrastructure & Hilt Worker Injection
To ensure background tasks can inject repositories and network clients cleanly without service locator anti-patterns:
1. `DukaanApplication` implements `Configuration.Provider`, supplying a `@Singleton` `HiltWorkerFactory`.
2. Background workers extend `CoroutineWorker` and are annotated with `@HiltWorker` and `@AssistedInject`:
   ```kotlin
   @HiltWorker
   class SyncWorker @AssistedInject constructor(
       @Assisted appContext: Context,
       @Assisted workerParams: WorkerParameters,
       // Repositories injected here
   ) : CoroutineWorker(appContext, workerParams)
   ```

## 3. Execution Constraints & Conventions
All background network tasks must adhere to defined execution constraints:
- **Network Constraint**: `NetworkType.CONNECTED` ensures tasks never spin or fail when the retailer has zero internet connection.
- **Battery Constraint**: `setRequiresBatteryNotLow(true)` prevents battery drain on budget Android devices.
- **Backoff & Retry Policy**:
  - `BackoffPolicy.EXPONENTIAL`: Failed tasks back off exponentially (15s, 30s, 60s, ...).
  - Maximum retry attempts are bounded (e.g. 3 attempts) to prevent infinite loops.

## 4. Sample Foundation Worker: `SyncWorker`
[`SyncWorker`](file:///c:/Dukan-AI/android/core/data/src/main/java/ai/dukaan/core/data/worker/SyncWorker.kt) validates the WorkManager infrastructure:
```kotlin
fun buildWorkRequest() = OneTimeWorkRequestBuilder<SyncWorker>()
    .setConstraints(
        Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .setRequiresBatteryNotLow(true)
            .build()
    )
    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 15, TimeUnit.SECONDS)
    .build()
```

## 5. Offline-First Sync Foundation
In upcoming stages (POS, Inventory, Khata):
- Every mutation commits to local Room tables and emits an entry into a local `outbox_events` table in the same SQLite transaction.
- WorkManager observes or periodically flushes pending outbox events using idempotent requests containing `idempotency_key` UUIDs.
- This guarantees reliable, at-least-once synchronization without transaction duplication.
