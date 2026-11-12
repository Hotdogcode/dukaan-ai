from fastapi import APIRouter
from pydantic import BaseModel, Field
from ..core.config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Service health state")
    service: str = Field(default="dukaanai-backend", description="Service identifier")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Liveness and readiness probe reporting service status.",
)
async def get_health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
    )
