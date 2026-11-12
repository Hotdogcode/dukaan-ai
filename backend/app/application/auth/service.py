"""
Authentication Application Service for DukaanAI.
Coordinates phone verification, user account provisioning,
rotating JWT refresh sessions, and secure logout.
"""

from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import (
    AuthenticationRequired,
    InvalidOTP,
    SessionRevoked,
    UserNotFound,
    UserSuspended,
    ValidationFailure,
)
from backend.app.core.security import (
    create_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
)
from backend.app.infrastructure.database.models import RefreshSession, User
from backend.app.infrastructure.otp.service import OTPService, normalize_phone_number
from backend.app.schemas.auth import TokenResponse
from backend.app.schemas.user import UserResponse


class AuthService:
    """Application service managing merchant authentication and token lifecycles."""

    @staticmethod
    def request_otp(raw_phone: str) -> dict[str, str | int]:
        """Dispatches an OTP verification code."""
        return OTPService.request_otp(raw_phone)

    @staticmethod
    def verify_otp_and_login(
        db: Session,
        otp: str,
        raw_phone: str | None = None,
        request_id: str | None = None,
        full_name: str | None = None,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """
        Verifies the submitted OTP, retrieves or provisions the user,
        and establishes an active JWT refresh session.
        """
        if request_id and not raw_phone:
            phone = OTPService.get_phone_for_request(request_id)
            if not phone:
                raise InvalidOTP("No active OTP request found for this request ID. Please request a new code.")
        elif raw_phone:
            phone = normalize_phone_number(raw_phone)
        else:
            raise ValidationFailure("Either request_id or phone_number must be provided.")

        OTPService.verify_otp(raw_phone=phone, submitted_otp=otp)

        # Lookup or provision User
        stmt = select(User).where(User.phone_number == phone)
        user = db.scalar(stmt)

        if not user:
            # First-time merchant registration
            user = User(
                phone_number=phone,
                full_name=full_name.strip() if full_name and full_name.strip() else "Store Merchant",
                password_hash=hash_password(generate_secure_token(16)),
                is_active=True,
            )
            db.add(user)
            db.flush()
        else:
            if not user.is_active:
                raise UserSuspended("This account is currently suspended or disabled.")

        # Establish Refresh Session
        raw_refresh_token = generate_secure_token(32)
        hashed_refresh_token = hash_token(raw_refresh_token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_session = RefreshSession(
            user_id=user.id,
            token_hash=hashed_refresh_token,
            expires_at=expires_at,
            revoked_at=None,
        )
        db.add(refresh_session)
        db.commit()
        db.refresh(user)
        db.refresh(refresh_session)

        # Issue Access Token
        access_token = create_access_token(user.id, refresh_session.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    def rotate_refresh_token(
        db: Session,
        raw_refresh_token: str,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """
        Validates the existing refresh token, revokes it, and issues a new token pair.
        Protects against token reuse attacks by revoking the entire session family if compromised.
        """
        token_hash = hash_token(raw_refresh_token)
        stmt = select(RefreshSession).where(RefreshSession.token_hash == token_hash)
        session_record = db.scalar(stmt)

        if not session_record:
            raise SessionRevoked("Invalid refresh token.")

        now = datetime.now(timezone.utc)
        if session_record.revoked_at is not None:
            # Token reuse detected! Revoke all sessions for this user for security
            db.execute(
                update(RefreshSession)
                .where(RefreshSession.user_id == session_record.user_id)
                .values(revoked_at=now)
            )
            db.commit()
            raise SessionRevoked("Refresh token reuse detected. All sessions have been revoked for your security.")

        expires_at = session_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            session_record.revoked_at = now
            db.commit()
            raise SessionRevoked("Refresh token has expired. Please sign in again.")

        # Revoke the old refresh token
        session_record.revoked_at = now

        # Fetch active user
        user = db.get(User, session_record.user_id)
        if not user or not user.is_active:
            db.commit()
            raise UserSuspended("User account is inactive or suspended.")

        # Create new rotating refresh session
        new_raw_token = generate_secure_token(32)
        new_session = RefreshSession(
            user_id=user.id,
            token_hash=hash_token(new_raw_token),
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            revoked_at=None,
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)

        # Issue new access token
        access_token = create_access_token(user.id, new_session.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    def logout(db: Session, raw_refresh_token: str | None = None, session_id: uuid.UUID | None = None) -> None:
        """Revokes the current refresh session."""
        now = datetime.now(timezone.utc)
        if raw_refresh_token:
            token_hash = hash_token(raw_refresh_token)
            stmt = select(RefreshSession).where(RefreshSession.token_hash == token_hash)
            record = db.scalar(stmt)
            if record and record.revoked_at is None:
                record.revoked_at = now
                db.commit()
        elif session_id:
            record = db.get(RefreshSession, session_id)
            if record and record.revoked_at is None:
                record.revoked_at = now
                db.commit()

    @staticmethod
    def logout_all_devices(db: Session, user_id: uuid.UUID) -> None:
        """Revokes all active refresh sessions for the user across all devices."""
        now = datetime.now(timezone.utc)
        db.execute(
            update(RefreshSession)
            .where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()
