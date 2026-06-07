"""Fixtures de pytest para el backend de activia-trace."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import Settings
from app.main import app


settings = Settings()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fixture que provee una sesión async de test y hace rollback al final."""
    test_engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )
    TestSessionLocal = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    session = TestSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        await test_engine.dispose()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Fixture de cliente HTTP async para tests de integración."""
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
