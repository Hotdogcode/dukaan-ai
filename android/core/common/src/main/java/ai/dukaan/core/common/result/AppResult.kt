package ai.dukaan.core.common.result

/**
 * Foundation result wrapper representing success or failure states.
 */
sealed interface AppResult<out T> {
    data class Success<out T>(val data: T) : AppResult<T>
    data class Error(val exception: Throwable, val message: String? = null) : AppResult<Nothing>
    data object Loading : AppResult<Nothing>
}
