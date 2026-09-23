# Conftest for pytest-asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncClient:
    # Use base_url without app parameter for httpx compatibility
    async with AsyncClient(base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session