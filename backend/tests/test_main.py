import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from core.config import settings

# Instruct pytest-asyncio to treat these as async tests
pytestmark = pytest.mark.asyncio

import pytest_asyncio

@pytest_asyncio.fixture
async def test_db_session():
    """
    Creates a database session bound to the active test loop.
    Disposes of the engine after the test completes.
    """
    engine = create_async_engine(settings.DATABASE_URL, future=True)
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session
    
    # Properly close the engine connections
    await engine.dispose()

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
