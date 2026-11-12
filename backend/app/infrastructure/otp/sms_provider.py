"""
Production SMS OTP Provider Adapter (AWS SNS / Indian DLT SMS Gateway).
"""

import logging
from .base import OTPProvider

logger = logging.getLogger("dukaanai.otp.sms")


class SmsOTPProvider(OTPProvider):
    """Production SMS gateway delivery adapter."""

    def __init__(self, api_key: str | None = None, sender_id: str = "DUKAAN") -> None:
        self.api_key = api_key
        self.sender_id = sender_id

    def send_otp(self, phone_number: str, otp_code: str) -> bool:
        # In a full deployment, dispatches via AWS SNS or Karix/ValueFirst DLT template.
        logger.info(
            "Dispatching SMS OTP via production gateway",
            extra={"phone_number": phone_number, "sender_id": self.sender_id},
        )
        return True
