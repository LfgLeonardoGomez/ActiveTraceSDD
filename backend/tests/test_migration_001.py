"""Tests de TDD para migración Alembic 001 — C-02 Task Group 4."""

import pytest
import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.core.database import Base

settings = Settings()


def _reset_database():
    """Limpia la base de datos de test para migraciones: drop all + borra alembic_version."""
    async def reset():
        engine = create_async_engine(settings.database_url, echo=False)
        async with engine.begin() as conn:
            # Limpiar alembic_version para que los tests de migración partan de cero
            await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
            for tbl in reversed(list(Base.metadata.tables.keys())):
                await conn.execute(text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))
        await engine.dispose()
    asyncio.run(reset())


class TestMigration001:
    """RED/GREEN/TRIANGULATE para migración 001_tenant."""

    def test_migration_creates_tenants_table(self):
        """RED: upgrade head crea tabla tenants."""
        from alembic import command
        from alembic.config import Config

        _reset_database()
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

        command.upgrade(alembic_cfg, "head")

        test_engine = create_async_engine(settings.database_url, echo=False)
        async def check():
            async with test_engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tenants')")
                )
                assert result.scalar() is True
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_migration_seeds_default_tenant(self):
        """GREEN: upgrade head inserta tenant default con slug 'default'."""
        from alembic import command
        from alembic.config import Config

        _reset_database()
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

        command.upgrade(alembic_cfg, "head")

        test_engine = create_async_engine(settings.database_url, echo=False)
        async def check():
            async with test_engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT slug, nombre, activo FROM tenants WHERE slug = 'default'")
                )
                row = result.fetchone()
                assert row is not None
                assert row.slug == "default"
                assert row.activo is True
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_migration_downgrade_removes_tenants_table(self):
        """TRIANGULATE: downgrade -1 elimina tabla tenants."""
        from alembic import command
        from alembic.config import Config

        _reset_database()
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

        command.upgrade(alembic_cfg, "head")
        command.downgrade(alembic_cfg, "-1")

        test_engine = create_async_engine(settings.database_url, echo=False)
        async def check():
            async with test_engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tenants')")
                )
                assert result.scalar() is False
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_migration_slug_is_unique(self):
        """TRIANGULATE: constraint UNIQUE en slug existe."""
        from alembic import command
        from alembic.config import Config

        _reset_database()
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

        command.upgrade(alembic_cfg, "head")

        test_engine = create_async_engine(settings.database_url, echo=False)
        async def check():
            async with test_engine.connect() as conn:
                # Insertar dos tenants con mismo slug debería fallar
                await conn.execute(
                    text("INSERT INTO tenants (id, nombre, slug, activo, created_at, updated_at) VALUES (gen_random_uuid(), 'A', 'dup', true, NOW(), NOW())")
                )
                await conn.commit()
                with pytest.raises(Exception):
                    await conn.execute(
                        text("INSERT INTO tenants (id, nombre, slug, activo, created_at, updated_at) VALUES (gen_random_uuid(), 'B', 'dup', true, NOW(), NOW())")
                    )
                    await conn.commit()
        asyncio.run(check())
        test_engine.sync_engine.dispose()
