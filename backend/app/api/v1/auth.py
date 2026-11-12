"""
Authentication and Session Endpoints for DukaanAI.
Handles phone-number OTP dispatch, verification, JWT issuing, rotation, and revocation.
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_user
from backend.app.application.auth.service import AuthService
from backend.app.infrastructure.database.models import User
from backend.app.infrastructure.database.session import get_db_session
from backend.app.schemas.auth import (
    LogoutRequest,
    OTPRequest,
    OTPResponse,
    OTPVerifyRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from backend.app.schemas.common import MessageResponse
from backend.app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/request-otp",
    response_model=OTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Phone OTP (Legacy)",
)
@router.post(
    "/otp/request",
    response_model=OTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Phone OTP",
)
def request_otp(payload: OTPRequest) -> OTPResponse:
    """Dispatches a 6-digit verification code to the given mobile number."""
    result = AuthService.request_otp(payload.phone_number)
    return OTPResponse(
        request_id=str(result["request_id"]),
        message=str(result["message"]),
        phone_number=str(result["phone_number"]),
        expires_in_seconds=int(result["expires_in_seconds"]),
        retry_after_seconds=int(result.get("retry_after_seconds", result.get("cooldown_seconds", 30))),
        cooldown_seconds=int(result["cooldown_seconds"]),
    )


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP & Sign In (Legacy)",
)
@router.post(
    "/otp/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP & Sign In",
)
def verify_otp(
    payload: OTPVerifyRequest,
    request: Request,
    db: Session = Depends(get_db_session),
) -> TokenResponse:
    """
    Verifies OTP, provisions or retrieves the merchant account,
    and returns a JWT Access Token and Rotating Refresh Token.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    return AuthService.verify_otp_and_login(
        db=db,
        otp=payload.otp,
        raw_phone=payload.phone_number,
        request_id=payload.request_id,
        full_name=payload.full_name,
        device_fingerprint=payload.device_fingerprint,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate Refresh Token",
)
def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db_session),
) -> TokenResponse:
    """
    Rotates the refresh token family and returns a new Access Token.
    Detects refresh token reuse and revokes compromised sessions.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    return AuthService.rotate_refresh_token(
        db=db,
        raw_refresh_token=payload.refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign Out Current Session",
)
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db_session),
) -> MessageResponse:
    """Revokes the current refresh session."""
    AuthService.logout(db, raw_refresh_token=payload.refresh_token)
    return MessageResponse(message="Successfully signed out.")


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign Out All Devices",
)
def logout_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> MessageResponse:
    """Revokes all active refresh sessions across all devices for the current user."""
    AuthService.logout_all_devices(db, current_user.id)
    return MessageResponse(message="All active sessions have been successfully revoked.")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current Authenticated User",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Returns the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)
