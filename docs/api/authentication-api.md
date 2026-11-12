# DukaanAI — Authentication API Reference

## 1. Request OTP
- **Endpoint:** `POST /api/v1/auth/otp/request` (Alias: `/request-otp`)
- **Summary:** Dispatches a 6-digit verification code to the merchant's mobile number.
- **Request Body:**
```json
{
  "phone_number": "9876543210"
}
```
- **Response (200 OK):**
```json
{
  "request_id": "4a7f0535-c49b-4632-a567-27b2b8006d9a",
  "message": "If the phone number is valid, an OTP verification code has been dispatched.",
  "phone_number": "+919876543210",
  "expires_in_seconds": 300,
  "retry_after_seconds": 30,
  "cooldown_seconds": 30
}
```
- **Error Responses:**
  - `429 Too Many Requests`: `OTP_COOLDOWN_ACTIVE` (Cooldown period active).

---

## 2. Verify OTP & Establish Session
- **Endpoint:** `POST /api/v1/auth/otp/verify` (Alias: `/verify-otp`)
- **Summary:** Verifies code, provisions user if new, and establishes JWT session.
- **Request Body:**
```json
{
  "request_id": "4a7f0535-c49b-4632-a567-27b2b8006d9a",
  "otp": "123456",
  "full_name": "Ramesh Gupta"
}
```
- **Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "d7a4f91e92d849419163be60...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": "e9bcf281-2c1a-4d9c-a111-97f2674e7123",
    "phone_number": "+919876543210",
    "full_name": "Ramesh Gupta",
    "is_active": true,
    "created_at": "2026-11-12T10:00:00Z"
  }
}
```

---

## 3. Refresh Access Token
- **Endpoint:** `POST /api/v1/auth/refresh`
- **Request Body:**
```json
{
  "refresh_token": "d7a4f91e92d849419163be60..."
}
```
- **Response (200 OK):** Returns new `access_token` and rotated `refresh_token`.

---

## 4. Logout / Session Revocation
- **Endpoint:** `POST /api/v1/auth/logout`
- **Request Body:**
```json
{
  "refresh_token": "d7a4f91e92d849419163be60..."
}
```
- **Response (200 OK):**
```json
{
  "message": "Session successfully terminated."
}
```

---

## 5. Get Current User Profile
- **Endpoint:** `GET /api/v1/auth/me`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response (200 OK):** Current merchant user object.
