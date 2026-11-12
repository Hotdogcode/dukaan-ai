"""
Application-wide domain and HTTP exception hierarchy for DukaanAI.
Guarantees consistent JSON error structures and safe, non-leaking messages.
"""

from typing import Any


class DukaanAIException(Exception):
    """Base class for all business and application exceptions."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []


class AuthenticationRequired(DukaanAIException):
    def __init__(self, message: str = "Authentication credentials were not provided or are invalid."):
        super().__init__(message=message, code="AUTHENTICATION_REQUIRED", status_code=401)


class InvalidCredentials(DukaanAIException):
    def __init__(self, message: str = "Invalid authentication credentials."):
        super().__init__(message=message, code="INVALID_CREDENTIALS", status_code=401)


class InvalidOTP(DukaanAIException):
    def __init__(self, message: str = "Invalid or incorrect OTP verification code."):
        super().__init__(message=message, code="INVALID_OTP", status_code=400)


class OTPExpired(DukaanAIException):
    def __init__(self, message: str = "OTP verification code has expired. Please request a new one."):
        super().__init__(message=message, code="OTP_EXPIRED", status_code=400)


class OTPMaxAttemptsExceeded(DukaanAIException):
    def __init__(self, message: str = "Maximum OTP verification attempts exceeded. Please request a new code."):
        super().__init__(message=message, code="OTP_MAX_ATTEMPTS_EXCEEDED", status_code=429)


class OTPCooldownActive(DukaanAIException):
    def __init__(self, retry_after_seconds: int = 60):
        super().__init__(
            message=f"Please wait {retry_after_seconds} seconds before requesting a new OTP.",
            code="OTP_COOLDOWN_ACTIVE",
            status_code=429,
            details=[{"retry_after_seconds": retry_after_seconds}],
        )


class SessionRevoked(DukaanAIException):
    def __init__(self, message: str = "Session has been revoked or expired. Please sign in again."):
        super().__init__(message=message, code="SESSION_REVOKED", status_code=401)


class UserNotFound(DukaanAIException):
    def __init__(self, message: str = "User account not found."):
        super().__init__(message=message, code="USER_NOT_FOUND", status_code=404)


class UserSuspended(DukaanAIException):
    def __init__(self, message: str = "User account is suspended or inactive."):
        super().__init__(message=message, code="USER_SUSPENDED", status_code=403)


class BusinessNotFound(DukaanAIException):
    def __init__(self, message: str = "Business not found or access denied."):
        super().__init__(message=message, code="BUSINESS_NOT_FOUND", status_code=404)


class BusinessAccessDenied(DukaanAIException):
    def __init__(self, message: str = "You are not an active member of this business."):
        super().__init__(message=message, code="BUSINESS_ACCESS_DENIED", status_code=403)


class StoreNotFound(DukaanAIException):
    def __init__(self, message: str = "Store not found or access denied."):
        super().__init__(message=message, code="STORE_NOT_FOUND", status_code=404)


class InsufficientPermissions(DukaanAIException):
    def __init__(self, permission: str | None = None):
        msg = f"Insufficient permissions to perform this operation. Required: {permission}" if permission else "Insufficient permissions."
        super().__init__(
            message=msg,
            code="INSUFFICIENT_PERMISSIONS",
            status_code=403,
            details=[{"required_permission": permission}] if permission else [],
        )


class ValidationFailure(DukaanAIException):
    def __init__(self, message: str = "Request validation failed.", details: list[dict[str, Any]] | None = None):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422, details=details)


class ResourceConflict(DukaanAIException):
    def __init__(self, message: str = "The requested resource already exists or conflicts with current state."):
        super().__init__(message=message, code="RESOURCE_CONFLICT", status_code=409)


class RateLimitExceeded(DukaanAIException):
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED", status_code=429)
