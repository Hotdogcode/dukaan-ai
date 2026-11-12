"""
Development OTP Provider for Local and Automated Testing.
Captures generated OTP codes in-memory without contacting external SMS gateways.
Strictly disabled in production.
"""

import logging
from backend.app.core.config import settings
from .base import OTPProvider

logger = logging.getLogger("dukaanai.otp.dev")


class DevOTPProvider(OTPProvider):
    """
    In-memory development OTP provider.
    Allows automated test suites and local developers to retrieve issued OTP codes.
    """

    def __init__(self) -> None:
        if settings.ENVIRONMENT == "production":
            raise RuntimeError("CRITICAL SECURITY ERROR: DevOTPProvider cannot be instantiated in production.")
        # Phone number -> latest plain OTP code mapping (only kept for dev/testing)
        self._sent_otps: dict[str, str] = {}

    def send_otp(self, phone_number: str, otp_code: str) -> bool:
        if settings.ENVIRONMENT == "production":
            raise RuntimeError("CRITICAL SECURITY ERROR: DevOTPProvider attempted in production.")

        self._sent_otps[phone_number] = otp_code
        logger.info(
            "Development OTP generated for recipient",
            extra={
                "phone_number": phone_number,
                # In debug/dev, log code for convenience if DEBUG is true
                "dev_otp": otp_code if settings.DEBUG else "***REDACTED***",
            },
        )
        return True

    def get_latest_otp(self, phone_number: str) -> str | None:
        """Inspects the latest sent OTP for a given phone number (test helper)."""
        return self._sent_otps.get(phone_number)

    def clear(self) -> None:
        """Clears all stored OTPs."""
        self._sent_otps.clear()
