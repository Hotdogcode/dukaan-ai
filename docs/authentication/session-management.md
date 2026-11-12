# DukaanAI — Session Management & Mutex Authenticator

## 1. Single-Flight Token Authenticator

In a reactive Android application with concurrent coroutines, multiple network requests can hit an expired access token (HTTP 401) at the exact same moment. Without synchronization, this creates a **refresh stampede**, resulting in multiple refresh calls, session race conditions, and accidental logout.

DukaanAI implements `TokenAuthenticator` (OkHttp `Authenticator`) with a Kotlin Coroutines `Mutex` lock to serialize token refresh.

```mermaid
sequenceDiagram
    autonumber
    participant Worker1 as Sync Worker Call
    participant Worker2 as UI Catalog Call
    participant Auth as TokenAuthenticator (Mutex)
    participant Backend as FastAPI Server

    par Simultaneous 401 Failures
        Worker1->>Auth: HTTP 401 Received
        Worker2->>Auth: HTTP 401 Received
    end

    Auth->>Auth: Worker1 acquires Mutex lock
    Note over Worker2,Auth: Worker2 suspended on Mutex
    
    Auth->>Backend: POST /api/v1/auth/refresh (single-flight)
    Backend-->>Auth: 200 OK (New Access Token T2)
    Auth->>Auth: Save T2 in SecureTokenStorage
    Auth-->>Worker1: Retry original request with Bearer T2
    
    Auth->>Auth: Worker1 releases Mutex
    Auth->>Auth: Worker2 acquires Mutex
    Auth->>Auth: Detects current token T2 != original header T1
    Auth-->>Worker2: Immediately retry with Bearer T2 (No network refresh call!)
```

---

## 2. Session Revocation & Logout
When merchant logs out or session is terminated:
1. `POST /api/v1/auth/logout` revokes the refresh session in PostgreSQL.
2. `SecureTokenStorage.clearTokens()` wipes access and refresh tokens from Android KeyStore.
3. `UserPreferencesDataSource.clearSession()` wipes active tenant and store context.
4. Navigation resets back to `LoginRoute`.
