"""
Unit Tests for OTP Generation, Rate-Limiting, Hashing, and Attempt Thresholds.
"""

from datetime import datetime, timedelta, timezone
import pytest

from backend.app.core.config import settings
from backend.app.core.exceptions import (
    InvalidOTP,
    OTPCooldownActive,
    OTPExpired,
    OTPMaxAttemptsExceeded,
    ValidationFailure,
)
from backend.app.infrastructure.otp.dev_provider import DevOTPProvider
from backend.app.infrastructure.otp.service import OTPService, normalize_phone_number


def test_phone_number_normalization():
    """Verify E.164 normalization for Indian retail mobile numbers."""
    assert normalize_phone_number("9876543210") == "+919876543210"
    assert normalize_phone_number("+91 98765 43210") == "+919876543210"
    assert normalize_phone_number("09876543210") == "+919876543210"
    assert normalize_phone_number("+91-98765-43210") == "+919876543210"
    assert normalize_phone_number("+14155552671") == "+14155552671"

    with pytest.raises(ValidationFailure):
        normalize_phone_number("12345")  # Too short

    with pytest.raises(ValidationFailure):
        normalize_phone_number("abcdefghij")  # Non-numeric


def test_otp_request_and_dispatch():
    """Verify OTP generation and storage in dev provider."""
    phone = "9876543210"
    response = OTPService.request_otp(phone)

    assert response["phone_number"] == "+919876543210"
    assert response["expires_in_seconds"] == settings.OTP_EXPIRE_SECONDS

    provider = OTPService.get_provider()
    assert isinstance(provider, DevOTPProvider)
    otp_code = provider.get_latest_otp("+919876543210")
    assert otp_code is not None
    assert len(otp_code) == 6
    assert otp_code.isdigit()


def test_successful_otp_verification():
    """Verify correct OTP validates and purges from active storage to prevent replay."""
    phone = "9876543210"
    OTPService.request_otp(phone)
    provider = OTPService.get_provider()
    code = provider.get_latest_otp("+919876543210")

    assert OTPService.verify_otp(phone, code) is True

    # Replay attempt must fail as OTP was purged
    with pytest.raises(InvalidOTP):
        OTPService.verify_otp(phone, code)


def test_incorrect_otp_tracks_attempts():
    """Verify incorrect OTP increments attempts and eventually locks out."""
    phone = "9876543210"
    OTPService.request_otp(phone)

    # Submit wrong OTP
    with pytest.raises(InvalidOTP) as exc_info:
        OTPService.verify_otp(phone, "000000")
    assert "remaining" in str(exc_info.value).lower()

    # Exhaust remaining attempts up to max
    for _ in range(settings.OTP_MAX_ATTEMPTS - 2):
        with pytest.raises(InvalidOTP):
            OTPService.verify_otp(phone, "111111")

    # Final wrong attempt triggers OTPMaxAttemptsExceeded
    with pytest.raises(OTPMaxAttemptsExceeded):
        OTPService.verify_otp(phone, "222222")


def test_otp_cooldown_rate_limit():
    """Verify rapid consecutive OTP requests are throttled."""
    phone = "9876543210"
    OTPService.request_otp(phone)

    # Immediate second request must trigger cooldown
    with pytest.raises(OTPCooldownActive) as exc_info:
        OTPService.request_otp(phone)
    assert exc_info.value.status_code == 429


def test_expired_otp_is_rejected():
    """Verify expired OTP codes cannot be verified."""
    phone = "9876543210"
    OTPService.request_otp(phone)
    normalized = "+919876543210"

    # Simulate passage of time
    record = OTPService._storage[normalized]
    record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)

    provider = OTPService.get_provider()
    code = provider.get_latest_otp(normalized)

    with pytest.raises(OTPExpired):
        OTPService.verify_otp(phone, code)
