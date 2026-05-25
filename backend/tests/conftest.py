import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402

settings.DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/verity_test"
settings.SECRET_KEY = "test-secret-key-change-in-production-override-for-testing-only"
settings.JWT_ALGORITHM = "HS256"
settings.REDIS_URL = "redis://localhost:6379/0"

import app.services.auth_service as auth_svc  # noqa: E402

auth_svc._is_token_blacklisted = AsyncMock(return_value=False)
auth_svc.invalidate_refresh_family = AsyncMock(return_value=None)
auth_svc.store_refresh_token_family = AsyncMock(return_value=None)

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

test_engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client):
    """Register a test org and return auth headers."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "display_name": "Test User",
            "organization_name": "Test Org",
        },
    )
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    data = resp.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def auth_data(client):
    """Register a test org and return full auth data."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test2@example.com",
            "password": "testpass123",
            "display_name": "Test User 2",
            "organization_name": "Test Org 2",
        },
    )
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    return resp.json()
