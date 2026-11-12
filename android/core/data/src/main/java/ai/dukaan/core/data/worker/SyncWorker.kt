package ai.dukaan.core.data.worker

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkerParameters
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import timber.log.Timber
import java.util.concurrent.TimeUnit

/**
 * Sample no-op worker validating WorkManager + Hilt injection infrastructure,
 * retry strategies, and execution constraints.
 */
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        Timber.i("SyncWorker: Starting sample no-op synchronization task.")
        return try {
            // Foundation placeholder: Sync logic will be implemented in sync engine
            Timber.i("SyncWorker: Synchronization validation succeeded.")
            Result.success()
        } catch (e: Exception) {
            Timber.e(e, "SyncWorker: Synchronization task failed.")
            if (runAttemptCount < 3) Result.retry() else Result.failure()
        }
    }

    companion object {
        const val WORK_NAME = "ai.dukaan.core.data.worker.SyncWorker"

        fun buildWorkRequest() = OneTimeWorkRequestBuilder<SyncWorker>()
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .setRequiresBatteryNotLow(true)
                    .build()
            )
            .setBackoffCriteria(
                BackoffPolicy.EXPONENTIAL,
                15,
                TimeUnit.SECONDS,
            )
            .build()
    }
}
