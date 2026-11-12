# Logging and Observability

## Overview
DukaanAI implements structured JSON logging designed for production monitoring, distributed tracing, and automated log analysis (AWS CloudWatch, Datadog, ELK). Every log record carries request correlation metadata and scrubs sensitive data before output.

## Architecture

### 1. Request Correlation (`X-Request-ID`)
The `RequestCorrelationMiddleware` (`backend/app/core/middleware.py`) handles request tracing:
- Inspects incoming HTTP requests for an existing `X-Request-ID` header.
- If absent, generates a new cryptographic UUID4.
- Stores the ID in a Python `contextvars.ContextVar` (`request_id_ctx_var`).
- Attaches the ID as an HTTP response header `X-Request-ID` on all responses.
- Allows clients to cite their `request_id` during support requests and bug triage.

### 2. Structured JSON Formatter
The `JSONLogFormatter` in `backend/app/core/logging.py`:
- Formats log entries as single-line JSON objects with timestamps in ISO 8601 UTC.
- Automatically extracts `request_id` from `request_id_ctx_var`.
- Includes log level (`INFO`, `WARNING`, `ERROR`), module name, function name, and line number.
- Includes exception tracebacks when `exc_info` is present.

Example log output:
```json
{
  "timestamp": "2026-11-12T06:38:25.123456Z",
  "level": "INFO",
  "name": "backend.app.api.dependencies.auth",
  "message": "User verified tenant membership",
  "request_id": "c1f7b920-53bc-4ad1-a189-9b936d8928ee",
  "user_id": "e4587dbb-2ce3-4fcf-84cf-8d96075fbdc1",
  "business_id": "90d1bf4f-2f88-468e-b8d2-4e4ad1ceb836"
}
```

### 3. Sensitive Data Scrubbing
To comply with security best practices and prevent leaking PII, OTPs, or credentials into centralized logging systems:
- The logging layer recursively traverses dictionary and parameter payloads before logging.
- Any key matching sensitive patterns (`otp`, `password`, `token`, `authorization`, `secret`, `hash`) is automatically redacted and replaced with `"[REDACTED]"`.
- Raw plain OTPs are NEVER written to logs, console output, or database records.

## Health and Readiness Endpoints
- `GET /health`: Liveness probe verifying the HTTP application is alive and responding.
- `GET /health/ready`: Readiness probe actively querying the database via `SELECT 1`.
  - Returns `{"status": "ready", "database": "connected"}` with HTTP 200 when ready.
  - Returns `{"status": "unhealthy", "database": "disconnected"}` with HTTP 503 if the database is unreachable, enabling container orchestrators (Docker, Kubernetes) to route traffic safely.
