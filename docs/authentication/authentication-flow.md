# DukaanAI — Authentication Flow Architecture

## 1. Overview
DukaanAI employs a passwordless, phone-first OTP authentication protocol tailored for Indian kirana and small retail merchants. The flow eliminates credential friction while ensuring cryptographic security, session revocability, and tenant scoping.

---

## 2. End-to-End Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Merchant as Store Merchant
    participant App as Android Client (Jetpack Compose)
    participant SecStore as SecureTokenStorage (Android Keystore)
    participant AuthAPI as FastAPI Auth Service
    participant SMS as SMS Gateway (Dev/Cloud Provider)
    participant DB as PostgreSQL Database

    Merchant->>App: Enters 10-digit mobile (+91)
    App->>AuthAPI: POST /api/v1/auth/otp/request { phone_number }
    AuthAPI->>AuthAPI: Enforce 30s Cooldown & Rate Limits
    AuthAPI->>SMS: Dispatch 6-digit cryptographically secure OTP
    SMS-->>Merchant: SMS arrives with OTP code
    AuthAPI-->>App: 200 OK { request_id, expires_in: 300s, retry_after: 30s }
    
    Merchant->>App: Submits 6-digit OTP code
    App->>AuthAPI: POST /api/v1/auth/otp/verify { request_id, otp }
    AuthAPI->>AuthAPI: Verify HMAC-SHA256 digest in constant time
    AuthAPI->>DB: Query or Provision User Record
    AuthAPI->>DB: Insert RefreshSession with SHA-256 token hash
    AuthAPI-->>App: 200 OK { access_token, refresh_token, user }
    
    App->>SecStore: Encrypt & Store tokens (AES-256 GCM)
    App->>AuthAPI: GET /api/v1/businesses
    alt User has no businesses
        App-->>Merchant: Navigate to Business Onboarding Flow
    else User has active business
        App-->>Merchant: Restore BusinessContext & Navigate to Dashboard
    end
```

---

## 3. Client-Side Lifecycle & Session Restoration

```mermaid
stateDiagram-v2
    [*] --> SplashCheck
    SplashCheck --> CheckKeystore: Inspect SecureTokenStorage
    CheckKeystore --> VerifySession: Access Token Found
    CheckKeystore --> AttemptRefresh: Access Token Absent / Expired
    
    AttemptRefresh --> RefreshTokenCall: POST /api/v1/auth/refresh
    RefreshTokenCall --> FetchBusinesses: 200 OK (Tokens Rotated)
    RefreshTokenCall --> LoginScreen: 401 Unauthorized / Revoked
    
    VerifySession --> FetchBusinesses: GET /api/v1/businesses
    FetchBusinesses --> RouteDashboard: Has >= 1 Active Business
    FetchBusinesses --> RouteOnboarding: Has 0 Businesses
    FetchBusinesses --> OfflineCacheCheck: Network Failure (Offline)
    
    OfflineCacheCheck --> RouteDashboard: Cached BusinessContext Exists
    OfflineCacheCheck --> LoginScreen: No Cached Session
```

---

## 4. Key Security Invariants
1. **Never Log Sensitive Data:** Phone numbers are masked (`+91 98765*****`), OTPs and tokens are strictly excluded from structured logs and interceptors.
2. **Single-Flight Authenticator Mutex:** When access tokens expire, concurrent API requests queue on an in-memory Mutex in `TokenAuthenticator`. Only one refresh request executes; subsequent requests replay with the rotated token without infinite 401 loops.
3. **Replay Attack Elimination:** OTP codes are purged from server-side memory immediately upon successful verification.
