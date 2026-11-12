# Networking Architecture

## 1. Overview
The networking layer in [`:core:network`](file:///c:/Dukan-AI/android/core/network) provides an asynchronous, type-safe, and observable HTTP client infrastructure designed to integrate seamlessly with the DukaanAI FastAPI backend.

```
                      +-----------------------------+
                      |   Domain Use Cases & Repos  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    Retrofit REST Client     |
                      |   (Kotlinx Serialization)   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |      OkHttpClient Engine    |
                      |  - 15s Connect / 30s Read   |
                      +--------------+--------------+
                                     |
         +---------------------------+---------------------------+
         |                           |                           |
         v                           v                           v
+------------------+       +-------------------+       +--------------------+
|  RequestId       |       |  AuthInterceptor  |       | SafeLogging        |
|  Interceptor     |       |  - Bearer Token   |       | Interceptor        |
|  (X-Request-ID)  |       |  - X-Business-ID  |       | (Scrubbed secrets) |
+------------------+       +-------------------+       +--------------------+
```

## 2. Security and Safe Logging
To prevent credential leakage in logs, monitoring, or bug reports:
- The `SafeLoggingInterceptor` actively filters sensitive paths (e.g. `/auth/otp`, `/auth/token`, `/auth/verify`, `/auth/login`).
- `Authorization` headers and raw request/response bodies on sensitive endpoints are strictly excluded from logs.
- Plaintext OTPs, tokens, and customer contact credentials are never logged.

## 3. Distributed Request Correlation (`X-Request-ID`)
`RequestIdInterceptor` automatically attaches a unique UUID4 header `X-Request-ID` to every outbound network call.
- If the backend encounters an error, the correlation UUID is embedded in the response error envelope.
- This provides end-to-end distributed traceability between the Android client logs and the backend PostgreSQL/FastAPI logs.

## 4. Multi-Tenant Authorization Interceptor
`AuthInterceptor` collaborates with `AuthTokenProvider`:
- Injects `Authorization: Bearer <access_token>` on authenticated endpoints.
- Injects `X-Business-ID: <uuid>` to satisfy backend tenant isolation and PostgreSQL Row-Level Security (RLS) constraints.

## 5. Backend Error Mapping (`NetworkErrorEnvelope`)
Errors returned by the FastAPI backend conform to the standardized error envelope:
```json
{
  "code": "INVALID_CREDENTIALS",
  "message": "Incorrect phone number or OTP",
  "details": {},
  "request_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
}
```
In Android, this is parsed via Kotlinx Serialization into `NetworkErrorEnvelope`, allowing ViewModels to render localized, user-friendly error banners without crashing on unexpected payloads.

## 6. Connectivity Abstraction (`ConnectivityObserver`)
Network reachability is abstracted through [`ConnectivityObserver`](file:///c:/Dukan-AI/android/core/network/src/main/java/ai/dukaan/core/network/connectivity/NetworkConnectivityObserver.kt):
- Employs Android `ConnectivityManager.NetworkCallback` with Kotlin Coroutines `callbackFlow`.
- Emits real-time `ConnectivityStatus` (`AVAILABLE`, `LOSING`, `LOST`, `UNAVAILABLE`).
- ViewModels and UI banners observe this stream to notify the shop owner when operating in offline mode.
