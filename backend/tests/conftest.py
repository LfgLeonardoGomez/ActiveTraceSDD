"""Fixtures de pytest para el backend de activia-trace."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import delete

from app.core.config import Settings
from app.core.database import Base, init_db
from app.main import app

settings = Settings()


@pytest_asyncio.fixture
async def db_engine():
    """Fixture de engine de base de datos para tests (function-scoped)."""
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Fixture que provee una sesión async de test, crea tablas y hace rollback/cleanup."""
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(
        db_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    session = TestSessionLocal()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
        # Limpieza: drop all tables
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Fixture de cliente HTTP async para tests de integración."""
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest_asyncio.fixture
async def default_tenant(db_session: AsyncSession):
    """Fixture que crea un tenant default para tests."""
    from app.models.tenant import Tenant
    tenant = Tenant(
        nombre="Default Tenant",
        slug="default",
        activo=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant
