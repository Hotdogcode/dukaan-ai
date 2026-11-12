"""
Abstract Base Class for OTP Notification Providers.
"""

from abc import ABC, abstractmethod


class OTPProvider(ABC):
    """Interface for delivering OTP verification codes to mobile devices."""

    @abstractmethod
    def send_otp(self, phone_number: str, otp_code: str) -> bool:
        """
        Sends an OTP code to the target phone number.
        Returns True if the transmission succeeded, False otherwise.
        """
        pass
