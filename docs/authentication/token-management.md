# DukaanAI — Token Management & Keystore Encryption

## 1. Token Hierarchy & Lifetime

DukaanAI utilizes a dual-token asymmetric lifecycle:
1. **Access Token (Short-Lived):**
   - Standard: Signed JWT (HS256)
   - Lifetime: 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 15`)
   - Claims: `sub` (User UUID), `type` ("access"), `exp`, `iat`
2. **Refresh Token (Long-Lived, Rotating):**
   - Standard: 256-bit cryptographically secure random token (`secrets.token_urlsafe(32)`)
   - Lifetime: 30 days (`REFRESH_TOKEN_EXPIRE_DAYS = 30`)
   - Persistence: Server stores `SHA-256(refresh_token)` in `refresh_sessions` table.

---

## 2. Refresh Token Rotation (RTR)
Every call to `POST /api/v1/auth/refresh`:
- Validates that the submitted token exists, matches `token_hash`, and is not expired or revoked.
- Atomically marks the prior session `is_revoked = True`.
- Generates a completely new refresh token and access token pair.
- Detects token reuse: if a revoked refresh token is submitted, all active sessions for that user are immediately flagged and revoked (compromise defense).

```mermaid
sequenceDiagram
    autonumber
    participant App as Android Client
    participant Auth as Auth Service
    participant DB as RefreshSessions Table

    App->>Auth: POST /api/v1/auth/refresh { refresh_token_A }
    Auth->>DB: SELECT WHERE token_hash = SHA256(A)
    alt Session Valid
        Auth->>DB: UPDATE SET is_revoked = true (A)
        Auth->>DB: INSERT session (B, SHA256(B))
        Auth-->>App: 200 OK { access_token_2, refresh_token_B }
    else Session Already Revoked (Replay Attack)
        Auth->>DB: UPDATE ALL sessions SET is_revoked = true WHERE user_id = X
        Auth-->>App: 401 Unauthorized (Session Compromised)
    end
```

---

## 3. Android Keystore Hardware Encryption

Tokens are never written in plaintext to disk, SharedPreferences, or DataStore.
- **Master Key:** Stored inside Android KeyStore (`DukaanMasterKey`), generated via `KeyGenParameterSpec` with AES-256 in GCM mode without padding.
- **Storage Format:** Ciphertext and 12-byte initialization vector (IV) are encoded as `Base64(IV):Base64(Ciphertext)` and written to isolated private preferences.
- **Hardware Backed:** Backed by Secure Element (SE) / StrongBox / ARM TrustZone on supported modern Android hardware.

```mermaid
graph TD
    PlainText["Plaintext Access / Refresh Token"] --> AES["Cipher.init(ENCRYPT, AndroidKeyStore MasterKey)"]
    AES --> Payload["Base64(IV) : Base64(Ciphertext)"]
    Payload --> Disk["Private Encrypted SharedPreferences"]
    Disk --> Read["Base64 Decode IV + Ciphertext"]
    Read --> Decrypt["Cipher.init(DECRYPT, MasterKey, GCMParameterSpec)"]
    Decrypt --> Restored["Restored Token in Memory"]
```
