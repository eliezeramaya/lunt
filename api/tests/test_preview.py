import pytest
from httpx import AsyncClient

from api.main import app


@pytest.mark.asyncio
async def test_preview_endpoint_not_found():
    """Test preview endpoint with non-existent concept"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/preview",
            json={
                "concept_code": "NONEXISTENT",
                "location_code": "MX-CDMX",
            },
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
