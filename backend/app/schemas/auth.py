"""
Pydantic Schemas for Authentication and JWT Tokens.
"""

from pydantic import BaseModel, Field
from .user import UserResponse


class OTPRequest(BaseModel):
    """Payload to trigger an SMS/dev OTP dispatch."""
    phone_number: str = Field(description="10-digit Indian mobile number or E.164 format")


class OTPResponse(BaseModel):
    """Response returned upon OTP dispatch."""
    request_id: str
    expires_in_seconds: int = 300
    retry_after_seconds: int = 30
    cooldown_seconds: int = 30
    phone_number: str | None = None
    message: str = "OTP verification code dispatched."


class OTPVerifyRequest(BaseModel):
    """Payload to verify OTP and obtain JWT tokens."""
    request_id: str | None = Field(default=None, description="UUID returned from request-otp")
    phone_number: str | None = Field(default=None, description="Mobile number if request_id not provided")
    otp: str = Field(min_length=4, max_length=10)
    full_name: str | None = Field(default=None, description="Full name if new user registration")
    device_fingerprint: str | None = None


class TokenResponse(BaseModel):
    """Issued JWT Access and Refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900
    expires_in_seconds: int = 900
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Payload to rotate refresh token and obtain a new access token."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Payload to revoke active session."""
    refresh_token: str | None = None
