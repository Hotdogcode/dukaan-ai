package ai.dukaan.core.network.token

import ai.dukaan.core.model.AuthTokens

/**
 * Contract for hardware-backed, encrypted storage of authentication tokens.
 * Guarantees zero plain-text leaks to logs or standard storage.
 */
interface SecureTokenStorage {
    fun saveTokens(tokens: AuthTokens)
    fun getAccessToken(): String?
    fun getRefreshToken(): String?
    fun getTokens(): AuthTokens?
    fun clearTokens()
}
