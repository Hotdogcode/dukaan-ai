"""
HTTP Middlewares for DukaanAI: Request ID tracking, structured logging, and timing.
"""

import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from .logging import request_id_ctx, set_log_context

logger = logging.getLogger("dukaanai.http")


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Assigns or preserves X-Request-ID across the HTTP lifecycle.
    Populates context variables for structured JSON logging.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract or generate Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        set_log_context(request_id=request_id)

        start_time = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status_code = response.status_code if response else 500

            # Add header to response
            if response is not None:
                response.headers["X-Request-ID"] = request_id

            # Avoid logging noisy health checks in normal logs
            if request.url.path not in {"/health", "/ready"}:
                logger.info(
                    "HTTP Request Processed",
                    extra={
                        "http_method": request.method,
                        "http_path": request.url.path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                        "client_ip": request.client.host if request.client else None,
                    },
                )
