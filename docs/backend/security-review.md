# Security Review and Threat Model

## Overview
DukaanAI processes financial ledgers, inventory stock, customer khata credit, and business transaction histories for retail store owners. Security and tenant isolation are core architectural constraints. This document details the threat modeling, mitigation strategies, and security verification performed during the foundation implementation.

## Threat Model and Mitigations

### 1. Cross-Tenant Data Access (IDOR / BOLA)
- **Threat**: A malicious tenant crafts requests referencing another tenant's `business_id` or resource UUIDs to read or tamper with competitor data.
- **Mitigation**:
  - Multi-tier validation: Every tenant endpoint enforces `get_tenant_membership`, which parses `X-Business-ID`, verifies cryptographic signature on the access token, and confirms active membership in `business_users`.
  - Database-level RLS: In PostgreSQL, Row-Level Security policies filter table rows by `app.current_business_id`, preventing data leakage even in the case of missing application-level SQL clauses.
  - Verification: Automated security test `test_cross_tenant_isolation_enforced` verifies cross-tenant rejection with `403 Forbidden`.

### 2. OTP Brute-Force & Credential Stuffing
- **Threat**: An attacker attempts to guess 6-digit OTP codes via high-volume brute-force attempts.
- **Mitigation**:
  - Maximum 3 incorrect attempts per challenge: Reaching the limit permanently invalidates the challenge.
  - 60-second cooldown period per phone number: Requesting new OTPs is strictly rate-limited.
  - Short expiration window: OTPs expire in 5 minutes (300 seconds).
  - Peppered cryptographic hashing: Plaintext OTPs are never stored. The database stores `HMAC_SHA256(otp, OTP_PEPPER)`. An attacker with database read access cannot reverse the OTPs without the pepper secret.
  - Verification: `tests/unit/test_otp_service.py` comprehensively verifies cooldown limits, attempt locking, and expiration rejection.

### 3. Refresh Token Theft & Replay Attacks
- **Threat**: A refresh token is intercepted from network transit or client storage and replayed by an adversary.
- **Mitigation**:
  - Refresh Token Rotation: Every token refresh request revokes the presented refresh token and issues a new pair.
  - Token Family Invalidation: If a revoked refresh token is presented again (indicating token theft), the server immediately revokes all active refresh tokens belonging to that user session.
  - Hash-only storage: Refresh tokens are stored as `SHA-256` hashes in the `refresh_sessions` table.
  - Verification: `test_full_otp_authentication_flow` verifies session rotation and device binding.

### 4. Privilege Escalation & Role Violation
- **Threat**: A cashier or staff member invokes manager/owner-restricted endpoints (such as adding staff members or modifying financial/business settings).
- **Mitigation**:
  - Explicit role-based permissions matrix defined in `backend/app/core/security.py`.
  - Dependency `require_permission(Permission.BUSINESS_UPDATE)` or `Permission.USER_INVITE` enforces permission requirements at the route declaration level.
  - Inactive business users are barred immediately.
  - Verification: `test_cashier_role_restrictions` verifies cashiers attempting to invite members are rejected with `403 Forbidden`.

### 5. Sensitive Data Exposure in Logs & Exceptions
- **Threat**: Passwords, OTP codes, session tokens, or internal database stack traces appear in application logs or client error responses.
- **Mitigation**:
  - Recursive scrubbing in `backend/app/core/logging.py`: All log fields matching sensitive patterns (`otp`, `password`, `token`, `secret`) are replaced with `"[REDACTED]"`.
  - Sanitized error responses: In non-development environments, unhandled exceptions return a standardized error code `INTERNAL_SERVER_ERROR` with a generic message, hiding raw database queries and exceptions.

## Secrets Management
- All sensitive cryptographic keys (`JWT_SECRET_KEY`, `OTP_PEPPER`, `DATABASE_URL`) are read via environment variables.
- Production validator in `backend/app/core/config.py` enforces minimum 32-character key length and prevents using default dev secrets in production environments.
