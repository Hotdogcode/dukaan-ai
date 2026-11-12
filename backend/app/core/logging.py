import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any
from .config import settings

# Context variables for request-scoped correlation
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
user_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_id", default=None)
business_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("business_id", default=None)

SENSITIVE_KEYS = {
    "otp",
    "otp_code",
    "password",
    "hashed_password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "secret",
    "jwt_secret",
}


def scrub_sensitive_data(data: Any) -> Any:
    """Recursively scrub sensitive keys from log dictionaries and payloads."""
    if isinstance(data, dict):
        return {
            k: "***REDACTED***" if any(s in k.lower() for s in SENSITIVE_KEYS) else scrub_sensitive_data(v)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [scrub_sensitive_data(item) for item in data]
    return data


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter with request context and security redaction."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.SERVICE_NAME,
            "environment": settings.ENVIRONMENT,
            "request_id": request_id_ctx.get(),
            "user_id": user_id_ctx.get(),
            "business_id": business_id_ctx.get(),
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Append extra fields, scrubbing any sensitive values
        for key, value in record.__dict__.items():
            if key not in {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "id",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            }:
                log_record[key] = scrub_sensitive_data(value)

        return json.dumps(log_record)


def setup_logging() -> None:
    """Configures application root logging based on environment configuration."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL.upper())

    # Clear existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)


def set_log_context(request_id: str | None = None, user_id: str | None = None, business_id: str | None = None) -> None:
    """Helper to populate contextual variables for structured logging."""
    if request_id is not None:
        request_id_ctx.set(request_id)
    if user_id is not None:
        user_id_ctx.set(str(user_id))
    if business_id is not None:
        business_id_ctx.set(str(business_id))
