# Error Handling Architecture

## Overview
DukaanAI provides a unified, deterministic, and security-sanitized error handling mechanism across all API surfaces. Error responses follow a consistent JSON envelope schema, guaranteeing predictable client-side error handling on the Android client while preventing internal server details or database stack traces from leaking to clients.

## Standard Error Response Schema
Every error response returns the following JSON envelope format:
```json
{
  "code": "RESOURCE_NOT_FOUND",
  "message": "Business with id 6ba7b810-9dad-11d1-80b4-00c04fd430c8 not found",
  "details": {},
  "request_id": "c1f7b920-53bc-4ad1-a189-9b936d8928ee"
}
```

### Response Envelope Fields
- `code` (string): Machine-readable uppercase error token (e.g., `VALIDATION_ERROR`, `INVALID_CREDENTIALS`, `FORBIDDEN_BUSINESS_ACCESS`, `RESOURCE_NOT_FOUND`, `RATE_LIMIT_EXCEEDED`, `INTERNAL_SERVER_ERROR`).
- `message` (string): Human-readable descriptive explanation suitable for client logging and diagnosis.
- `details` (dict / object): Optional contextual structured metadata (e.g., field-level validation errors, remaining cooldown seconds, parameter names).
- `request_id` (string): Correlation UUID injected by `RequestCorrelationMiddleware` (matches the `X-Request-ID` response header) to cross-reference server-side logs.

## Exception Hierarchy
The exception hierarchy is defined in `backend/app/core/exceptions.py`:
- `DukaanAIException` (Base Exception)
  - `AuthenticationRequiredException` (`HTTP 401`, code: `AUTHENTICATION_REQUIRED`)
  - `InvalidCredentialsException` (`HTTP 401`, code: `INVALID_CREDENTIALS`)
  - `TokenExpiredException` (`HTTP 401`, code: `TOKEN_EXPIRED`)
  - `InvalidTokenException` (`HTTP 401`, code: `INVALID_TOKEN`)
  - `PermissionDeniedException` (`HTTP 403`, code: `PERMISSION_DENIED`)
  - `ForbiddenBusinessAccessException` (`HTTP 403`, code: `FORBIDDEN_BUSINESS_ACCESS`)
  - `ResourceNotFoundException` (`HTTP 404`, code: `RESOURCE_NOT_FOUND`)
  - `ConflictException` (`HTTP 409`, code: `CONFLICT`)
  - `ValidationException` (`HTTP 422`, code: `VALIDATION_ERROR`)
  - `RateLimitExceededException` (`HTTP 429`, code: `RATE_LIMIT_EXCEEDED`)

## Global Exception Handlers
In `backend/app/main.py`:
1. **`DukaanAIException` Handler**:
   - Maps the custom domain exception to its corresponding HTTP status code.
   - Formats the response using `StandardErrorResponse`.
   - Logs the warning with the correlation `request_id`.
2. **FastAPI `RequestValidationError` Handler**:
   - Intercepts Pydantic schema validation failures.
   - Maps errors into structured `details["field_errors"]`.
   - Returns `HTTP 422 Unprocessable Entity` with code `VALIDATION_ERROR`.
3. **Unhandled `Exception` Handler**:
   - Catches unexpected runtime crashes and database errors.
   - Logs the full stack trace server-side with structured logger and `request_id`.
   - In production (`ENVIRONMENT != "development"`), sanitizes the output and returns a generic message (`"An unexpected error occurred. Please try again later."`) with code `INTERNAL_SERVER_ERROR` to eliminate any sensitive leakages.
