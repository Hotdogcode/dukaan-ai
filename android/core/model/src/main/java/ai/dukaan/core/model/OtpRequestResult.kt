package ai.dukaan.core.model

/**
 * Result of an OTP dispatch request.
 */
data class OtpRequestResult(
    val requestId: String?,
    val phoneNumber: String,
    val expiresInSeconds: Int,
    val retryAfterSeconds: Int,
    val message: String,
)
