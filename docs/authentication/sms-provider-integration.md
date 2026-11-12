# DukaanAI — SMS Gateway Provider Integration

## 1. Gateway Abstraction
DukaanAI decouples OTP generation and business logic from SMS delivery providers via the `OTPProvider` interface.

```python
class OTPProvider(ABC):
    @abstractmethod
    def send_otp(self, phone_number: str, otp_code: str) -> bool:
        """Dispatches an OTP verification code."""
        pass
```

---

## 2. Supported Environments
1. **Development & Local Testing (`DevOTPProvider`):**
   - Keeps latest dispatched OTP in an in-memory thread-safe dictionary.
   - Logs masked delivery to structured logger: `[DEV_OTP] Dispatched verification code for phone +91 98765*****`.
   - Enables zero-cost local automated testing and emulator development without real SMS costs or telecommunication delays.
2. **Production Providers (`TwilioOTPProvider` / `ExotelOTPProvider` / `GupshupOTPProvider`):**
   - Pluggable via environment configuration (`SMS_PROVIDER = "exotel"` or `"twilio"`).
   - Compliant with Indian TRAI DLT regulations for transactional SMS templates.
