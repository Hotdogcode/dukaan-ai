package ai.dukaan.core.network.token

import ai.dukaan.core.model.AuthTokens
import android.content.Context
import android.content.SharedPreferences
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import dagger.hilt.android.qualifiers.ApplicationContext
import timber.log.Timber
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AndroidKeystoreTokenStorage @Inject constructor(
    @ApplicationContext private val context: Context,
) : SecureTokenStorage {

    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    init {
        ensureMasterKey()
    }

    private fun ensureMasterKey() {
        try {
            val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE)
            keyStore.load(null)
            if (!keyStore.containsAlias(KEY_ALIAS)) {
                val keyGenerator = KeyGenerator.getInstance(
                    KeyProperties.KEY_ALGORITHM_AES,
                    ANDROID_KEYSTORE,
                )
                val keyGenParameterSpec = KeyGenParameterSpec.Builder(
                    KEY_ALIAS,
                    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
                )
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .setKeySize(256)
                    .build()
                keyGenerator.init(keyGenParameterSpec)
                keyGenerator.generateKey()
            }
        } catch (e: Exception) {
            Timber.e(e, "Failed to initialize AndroidKeyStore key")
        }
    }

    private fun getSecretKey(): SecretKey? {
        return try {
            val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE)
            keyStore.load(null)
            val entry = keyStore.getEntry(KEY_ALIAS, null) as? KeyStore.SecretKeyEntry
            entry?.secretKey
        } catch (e: Exception) {
            Timber.e(e, "Failed to retrieve SecretKey from KeyStore")
            null
        }
    }

    private fun encrypt(plainText: String): String? {
        val secretKey = getSecretKey() ?: return null
        return try {
            val cipher = Cipher.getInstance(TRANSFORMATION)
            cipher.init(Cipher.ENCRYPT_MODE, secretKey)
            val iv = cipher.iv
            val encryptedBytes = cipher.doFinal(plainText.toByteArray(Charsets.UTF_8))
            // Format: Base64(iv):Base64(encrypted)
            val ivEncoded = Base64.encodeToString(iv, Base64.NO_WRAP)
            val cipherEncoded = Base64.encodeToString(encryptedBytes, Base64.NO_WRAP)
            "$ivEncoded:$cipherEncoded"
        } catch (e: Exception) {
            Timber.e(e, "Token encryption failed")
            null
        }
    }

    private fun decrypt(encryptedPayload: String?): String? {
        if (encryptedPayload.isNullOrBlank()) return null
        val parts = encryptedPayload.split(":")
        if (parts.size != 2) return null
        val secretKey = getSecretKey() ?: return null
        return try {
            val iv = Base64.decode(parts[0], Base64.NO_WRAP)
            val cipherBytes = Base64.decode(parts[1], Base64.NO_WRAP)
            val cipher = Cipher.getInstance(TRANSFORMATION)
            val spec = GCMParameterSpec(GCM_TAG_LENGTH_BITS, iv)
            cipher.init(Cipher.DECRYPT_MODE, secretKey, spec)
            String(cipher.doFinal(cipherBytes), Charsets.UTF_8)
        } catch (e: Exception) {
            Timber.e(e, "Token decryption failed")
            null
        }
    }

    override fun saveTokens(tokens: AuthTokens) {
        val encryptedAccess = encrypt(tokens.accessToken)
        val encryptedRefresh = encrypt(tokens.refreshToken)

        prefs.edit()
            .putString(KEY_ACCESS_TOKEN, encryptedAccess)
            .putString(KEY_REFRESH_TOKEN, encryptedRefresh)
            .putString(KEY_TOKEN_TYPE, tokens.tokenType)
            .putLong(KEY_EXPIRES_IN, tokens.expiresIn)
            .apply()
    }

    override fun getAccessToken(): String? {
        val encrypted = prefs.getString(KEY_ACCESS_TOKEN, null)
        return decrypt(encrypted)
    }

    override fun getRefreshToken(): String? {
        val encrypted = prefs.getString(KEY_REFRESH_TOKEN, null)
        return decrypt(encrypted)
    }

    override fun getTokens(): AuthTokens? {
        val access = getAccessToken()
        val refresh = getRefreshToken()
        if (access == null || refresh == null) return null
        val tokenType = prefs.getString(KEY_TOKEN_TYPE, "Bearer") ?: "Bearer"
        val expiresIn = prefs.getLong(KEY_EXPIRES_IN, 900L)
        return AuthTokens(
            accessToken = access,
            refreshToken = refresh,
            tokenType = tokenType,
            expiresIn = expiresIn,
        )
    }

    override fun clearTokens() {
        prefs.edit().clear().apply()
    }

    companion object {
        private const val PREFS_NAME = "dukaan_secure_tokens"
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val KEY_ALIAS = "DukaanMasterKey"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
        private const val GCM_TAG_LENGTH_BITS = 128

        private const val KEY_ACCESS_TOKEN = "enc_access_token"
        private const val KEY_REFRESH_TOKEN = "enc_refresh_token"
        private const val KEY_TOKEN_TYPE = "token_type"
        private const val KEY_EXPIRES_IN = "expires_in"
    }
}
