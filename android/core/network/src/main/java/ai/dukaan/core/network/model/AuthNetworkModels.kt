package ai.dukaan.core.network.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class OtpRequestNetwork(
    @SerialName("phone_number") val phoneNumber: String,
)

@Serializable
data class OtpResponseNetwork(
    @SerialName("request_id") val requestId: String? = null,
    @SerialName("message") val message: String,
    @SerialName("phone_number") val phoneNumber: String,
    @SerialName("expires_in_seconds") val expiresInSeconds: Int = 300,
    @SerialName("retry_after_seconds") val retryAfterSeconds: Int = 30,
    @SerialName("cooldown_seconds") val cooldownSeconds: Int = 30,
)

@Serializable
data class OtpVerifyNetwork(
    @SerialName("otp") val otp: String,
    @SerialName("phone_number") val phoneNumber: String? = null,
    @SerialName("request_id") val requestId: String? = null,
    @SerialName("full_name") val fullName: String? = null,
    @SerialName("device_fingerprint") val deviceFingerprint: String? = null,
)

@Serializable
data class RefreshTokenNetwork(
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("device_fingerprint") val deviceFingerprint: String? = null,
)

@Serializable
data class LogoutNetwork(
    @SerialName("refresh_token") val refreshToken: String,
)

@Serializable
data class UserResponseNetwork(
    @SerialName("id") val id: String,
    @SerialName("phone_number") val phoneNumber: String,
    @SerialName("full_name") val fullName: String? = null,
    @SerialName("is_active") val isActive: Boolean = true,
)

@Serializable
data class TokenResponseNetwork(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("token_type") val tokenType: String = "Bearer",
    @SerialName("expires_in") val expiresIn: Long = 900L,
    @SerialName("user") val user: UserResponseNetwork,
)

@Serializable
data class MessageResponseNetwork(
    @SerialName("message") val message: String,
)
