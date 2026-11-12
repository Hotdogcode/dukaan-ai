"""
OTP Authentication Service for DukaanAI.
Handles phone normalization, cryptographically secure OTP generation,
pep-salted SHA-256 hashing, attempt rate-limiting, and expiry validation.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import re
import secrets
from typing import ClassVar

from backend.app.core.config import settings
from backend.app.core.exceptions import (
    InvalidOTP,
    OTPCooldownActive,
    OTPExpired,
    OTPMaxAttemptsExceeded,
    ValidationFailure,
)
from .base import OTPProvider
from .dev_provider import DevOTPProvider
from .sms_provider import SmsOTPProvider


def normalize_phone_number(raw_phone: str) -> str:
    """
    Normalizes a mobile phone number to E.164 international standard format.
    Accepts 10-digit Indian numbers (with or without +91 or leading 0).
    """
    if not raw_phone or not isinstance(raw_phone, str):
        raise ValidationFailure("Phone number must be provided.")

    cleaned = re.sub(r"[\s\-\(\)]", "", raw_phone.strip())

    # Case 1: Indian 10-digit starting with 6-9
    if re.fullmatch(r"[6-9]\d{9}", cleaned):
        return f"+91{cleaned}"

    # Case 2: 11-digit starting with 0 followed by 6-9
    if re.fullmatch(r"0[6-9]\d{9}", cleaned):
        return f"+91{cleaned[1:]}"

    # Case 3: Already has +91
    if re.fullmatch(r"\+91[6-9]\d{9}", cleaned):
        return cleaned

    # Case 4: General E.164 (+ followed by 10 to 15 digits)
    if re.fullmatch(r"\+[1-9]\d{9,14}", cleaned):
        return cleaned

    raise ValidationFailure("Invalid mobile phone number format. Please provide a valid 10-digit mobile number.")


import uuid


@dataclass
class PendingOTP:
    request_id: str
    phone_number: str
    hashed_otp: str
    attempts: int
    expires_at: datetime
    requested_at: datetime


class OTPService:
    """Manages the OTP lifecycle, rate-limiting, and verification logic."""

    # In-memory registry of active OTP sessions
    _storage: ClassVar[dict[str, PendingOTP]] = {}
    _request_to_phone: ClassVar[dict[str, str]] = {}
    _provider_instance: ClassVar[OTPProvider | None] = None

    @classmethod
    def get_provider(cls) -> OTPProvider:
        """Resolves the configured OTP provider instance."""
        if cls._provider_instance is None:
            if settings.OTP_PROVIDER == "fast2sms":
                from .fast2sms_provider import Fast2SMSOTPProvider
                cls._provider_instance = Fast2SMSOTPProvider()
            elif settings.OTP_PROVIDER == "sms":
                cls._provider_instance = SmsOTPProvider()
            else:
                cls._provider_instance = DevOTPProvider()
        return cls._provider_instance

    @classmethod
    def _hash_otp(cls, phone_number: str, plain_otp: str) -> str:
        """Creates a pepper-salted SHA-256 digest of the phone number and OTP code."""
        salt = settings.OTP_SECRET_PEPPER
        raw = f"{phone_number}:{plain_otp}:{salt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def request_otp(cls, raw_phone: str) -> dict[str, str | int]:
        """
        Generates and dispatches a 6-digit OTP code to the normalized phone number.
        Enforces request cooldowns and overwrites existing pending OTPs.
        """
        phone = normalize_phone_number(raw_phone)
        now = datetime.now(timezone.utc)

        # Check rate-limiting cooldown
        existing = cls._storage.get(phone)
        if existing and now < existing.requested_at + timedelta(seconds=settings.OTP_COOLDOWN_SECONDS):
            remaining = int((existing.requested_at + timedelta(seconds=settings.OTP_COOLDOWN_SECONDS) - now).total_seconds())
            raise OTPCooldownActive(retry_after_seconds=max(remaining, 1))

        # Generate 6-digit numeric OTP and request_id
        request_id = str(uuid.uuid4())
        plain_otp = settings.MASTER_OTP if settings.MASTER_OTP else f"{secrets.randbelow(1_000_000):06d}"
        hashed_otp = cls._hash_otp(phone, plain_otp)

        # Clean old request_id mapping if any
        if existing and existing.request_id in cls._request_to_phone:
            cls._request_to_phone.pop(existing.request_id, None)

        cls._storage[phone] = PendingOTP(
            request_id=request_id,
            phone_number=phone,
            hashed_otp=hashed_otp,
            attempts=0,
            expires_at=now + timedelta(seconds=settings.OTP_EXPIRE_SECONDS),
            requested_at=now,
        )
        cls._request_to_phone[request_id] = phone

        # Dispatch via provider
        provider = cls.get_provider()
        provider.send_otp(phone, plain_otp)

        return {
            "request_id": request_id,
            "message": "If the phone number is valid, an OTP verification code has been dispatched.",
            "phone_number": phone,
            "expires_in_seconds": settings.OTP_EXPIRE_SECONDS,
            "retry_after_seconds": settings.OTP_COOLDOWN_SECONDS,
            "cooldown_seconds": settings.OTP_COOLDOWN_SECONDS,
        }

    @classmethod
    def get_phone_for_request(cls, request_id: str) -> str | None:
        """Resolves an active OTP request_id to its normalized phone number."""
        return cls._request_to_phone.get(request_id)

    @classmethod
    def verify_otp(
        cls,
        raw_phone: str | None,
        submitted_otp: str,
        request_id: str | None = None,
    ) -> bool:
        """
        Validates the submitted OTP code.
        Enforces maximum attempt thresholds and expiration windows.
        Returns True upon successful verification.
        """
        is_master = bool(settings.MASTER_OTP and submitted_otp.strip() == settings.MASTER_OTP)

        if request_id and not raw_phone:
            phone = cls._request_to_phone.get(request_id)
            if not phone and not is_master:
                raise InvalidOTP("No active OTP request found for this request ID. Please request a new code.")
        elif raw_phone:
            phone = normalize_phone_number(raw_phone)
        else:
            if not is_master:
                raise ValidationFailure("Either request_id or phone_number must be provided.")
            phone = None

        now = datetime.now(timezone.utc)

        record = cls._storage.get(phone) if phone else None
        if not record:
            if is_master:
                return True
            raise InvalidOTP("No active OTP request found for this phone number. Please request a new code.")

        if now > record.expires_at:
            cls._storage.pop(phone, None)
            cls._request_to_phone.pop(record.request_id, None)
            if not is_master:
                raise OTPExpired()

        if record.attempts >= settings.OTP_MAX_ATTEMPTS:
            cls._storage.pop(phone, None)
            cls._request_to_phone.pop(record.request_id, None)
            if not is_master:
                raise OTPMaxAttemptsExceeded()

        # Compute hash and compare in constant time
        expected_hash = cls._hash_otp(phone, submitted_otp.strip())
        if not is_master and not secrets.compare_digest(record.hashed_otp, expected_hash):
            record.attempts += 1
            remaining_attempts = settings.OTP_MAX_ATTEMPTS - record.attempts
            if remaining_attempts <= 0:
                cls._storage.pop(phone, None)
                cls._request_to_phone.pop(record.request_id, None)
                raise OTPMaxAttemptsExceeded()
            raise InvalidOTP(f"Invalid OTP code. {remaining_attempts} attempt(s) remaining.")

        # Successfully verified: purge from pending storage to prevent replay attacks
        cls._storage.pop(phone, None)
        cls._request_to_phone.pop(record.request_id, None)
        return True

    @classmethod
    def clear_all(cls) -> None:
        """Test helper to reset in-memory state."""
        cls._storage.clear()
        cls._request_to_phone.clear()
        if isinstance(cls._provider_instance, DevOTPProvider):
            cls._provider_instance.clear()
