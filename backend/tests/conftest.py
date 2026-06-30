import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from core.database import get_db
from core.config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Creates a single database engine for each test."""
    engine = create_async_engine(settings.DATABASE_URL, future=True)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
def test_session_maker(test_engine):
    """Creates a session maker bound to the test engine."""
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_session_maker):
    """Creates a clean function-scoped database session for each test."""
    async with test_session_maker() as session:
        yield session

@pytest_asyncio.fixture(autouse=True)
async def override_db(test_session_maker):
    """
    Automatically overrides the FastAPI get_db dependency for all tests.
    Ensures endpoints get their own session connected to the test engine.
    """
    async def _get_test_db():
        async with test_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()
