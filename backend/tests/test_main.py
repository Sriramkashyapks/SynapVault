import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from main import app

# Instruct pytest-asyncio to treat these as async tests
pytestmark = pytest.mark.asyncio

async def test_health_check_returns_200():
    """
    Scenario 1: Verifies the FastAPI health check route works 
    and returns a successful connection state.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "connected"

async def test_db_connection_active(test_db_session):
    """
    Scenario 2: Asserts that the database connection is active
    using the loop-safe test database session.
    """
    result = await test_db_session.execute(text("SELECT 1"))
    value = result.scalar()
    assert value == 1
