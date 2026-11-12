import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_200(client: AsyncClient):
    """GET /health must return status 200 with healthy state."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "dukaanai-backend"


@pytest.mark.asyncio
async def test_openapi_docs_accessible(client: AsyncClient):
    """OpenAPI JSON spec must be generated and accessible."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert "paths" in spec
    assert "/health" in spec["paths"]
