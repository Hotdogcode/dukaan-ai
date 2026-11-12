"""
Main FastAPI Application Entrypoint for DukaanAI Backend.
Initializes middleware, master routers, structured logging, and global exception handlers.
"""

import os
import sys
from pathlib import Path

# Ensure both repository root and backend directory are in sys.path
_current_dir = Path(__file__).resolve().parent  # app/
_backend_dir = _current_dir.parent  # backend/
_root_dir = _backend_dir.parent  # repo root

for _p in [str(_root_dir), str(_backend_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.v1.health import router as root_health_router
from .api.v1.router import api_v1_router
from .core.config import settings
from .core.exceptions import DukaanAIException
from .core.logging import setup_logging
from .core.middleware import RequestCorrelationMiddleware

logger = logging.getLogger("dukaanai.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for initialization and cleanup."""
    setup_logging()
    logger.info(
        f"Starting {settings.PROJECT_NAME} [{settings.ENVIRONMENT}] on {settings.HOST}:{settings.PORT}",
        extra={"version": settings.VERSION, "env": settings.ENVIRONMENT},
    )
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


def create_application() -> FastAPI:
    """FastAPI application factory configuring security, routing, and error handlers."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Backend API and AI Orchestration Engine for DukaanAI Retail Assistant.",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 1. Add Request Correlation Middleware
    app.add_middleware(RequestCorrelationMiddleware)

    # 2. CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Global Exception Handlers
    @app.exception_handler(DukaanAIException)
    async def dukaanai_exception_handler(request: Request, exc: DukaanAIException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": request_id,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        formatted_details = []
        for error in exc.errors():
            loc = " -> ".join(str(l) for l in error.get("loc", []))
            formatted_details.append({
                "field": loc,
                "issue": error.get("msg"),
                "type": error.get("type"),
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The submitted payload failed validation.",
                    "request_id": request_id,
                    "details": formatted_details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "Unhandled internal exception encountered",
            exc_info=exc,
            extra={"request_id": request_id, "path": request.url.path},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                    "request_id": request_id,
                    "details": [],
                }
            },
        )

    # 4. Mount Master Routers
    # Direct Root health checks (/health and /ready)
    app.include_router(root_health_router)
    # Versioned API routes (/api/v1/...)
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
