package ai.dukaan.core.model

/**
 * Encapsulates access and refresh JWT tokens issued by backend.
 */
data class AuthTokens(
    val accessToken: String,
    val refreshToken: String,
    val tokenType: String = "Bearer",
    val expiresIn: Long = 900L,
)
