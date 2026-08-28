import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database import init_db


@pytest_asyncio.fixture(autouse=True)
async def initialize_database():
    await init_db()


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        response = await ac.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_overview_analytics():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        response = await ac.get("/api/v1/overview")

    assert response.status_code == 200
    data = response.json()
    assert "total_routes" in data
    assert "on_time_delivery_rate" in data


@pytest.mark.asyncio
async def test_list_routes():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        response = await ac.get("/api/v1/routes")

    assert response.status_code == 200
    assert isinstance(response.json(), list)