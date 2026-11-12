"""
Fast2SMS Gateway Integration for DukaanAI.
Delivers real-time SMS OTPs to Indian (+91) retail store numbers.
"""

import logging
import httpx
from backend.app.core.config import settings
from .base import OTPProvider

logger = logging.getLogger("dukaanai.otp.fast2sms")


class Fast2SMSOTPProvider(OTPProvider):
    """
    Production/Staging SMS OTP provider using Fast2SMS Quick OTP route.
    Delivers SMS to 10-digit Indian phone numbers without upfront DLT template delays.
    """

    FAST2SMS_ENDPOINT = "https://www.fast2sms.com/dev/bulkV2"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.FAST2SMS_API_KEY
        if not self.api_key:
            raise ValueError("FAST2SMS_API_KEY must be configured to use Fast2SMSOTPProvider.")

    def send_otp(self, phone_number: str, otp_code: str) -> bool:
        # Fast2SMS requires 10-digit phone number without country code
        ten_digit_phone = phone_number.replace("+91", "").strip()[-10:]
        headers = {
            "authorization": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "variables_values": otp_code,
            "route": "otp",
            "numbers": ten_digit_phone,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.FAST2SMS_ENDPOINT, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("return") is True:
                        masked_phone = f"+91 {ten_digit_phone[:2]}******{ten_digit_phone[-2:]}"
                        logger.info("Fast2SMS OTP dispatched successfully to %s", masked_phone)
                        return True
                    else:
                        logger.error("Fast2SMS gateway returned failure: %s", data.get("message"))
                        return False
                else:
                    logger.error("Fast2SMS HTTP %d error: %s", response.status_code, response.text)
                    return False
        except Exception as e:
            logger.error("Exception during Fast2SMS transmission: %s", str(e))
            return False
