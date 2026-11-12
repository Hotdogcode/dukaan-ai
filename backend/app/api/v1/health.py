"""
Health and Readiness Probes for DukaanAI.
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.infrastructure.database.session import get_db_session

router = APIRouter(tags=["Health & Readiness"])


@router.get("/health", summary="Liveness Probe")
def liveness_check() -> dict[str, str]:
    """Basic process liveness probe for orchestrators (K8s / Docker)."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ready", summary="Readiness Probe")
def readiness_check(db: Session = Depends(get_db_session)) -> JSONResponse:
    """Validates connectivity to required infrastructure dependencies (PostgreSQL)."""
    try:
        db.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "database": "connected",
                "version": settings.VERSION,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": "Database connectivity check failed.",
            },
        )
