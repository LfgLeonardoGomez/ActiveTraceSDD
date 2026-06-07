"""Tests de TDD para migración Alembic C-03.

Verifica que las tablas de auth existan y tengan las columnas requeridas.
"""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.core.database import Base

settings = Settings()


def _reset_database():
    """Limpia la base de datos de test para migraciones."""
    async def reset():
        engine = create_async_engine(settings.database_url, echo=False)
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
        await engine.dispose()
    asyncio.run(reset())


class TestMigrationC03:
    """Tests de migración C-03."""

    def test_c03_tables_exist(self):
        """RED: upgrade head crea tablas de auth."""
        from alembic import command
        from alembic.config import Config

        _reset_database()
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
        command.upgrade(alembic_cfg, "head")

        test_engine = create_async_engine(settings.database_url, echo=False)
        async def check():
            async with test_engine.connect() as conn:
                for tbl in [
                    "usuarios", "roles", "permisos",
                    "refresh_tokens", "password_reset_tokens",
                    "two_factor_enrollments", "rate_limit_buckets",
                ]:
                    result = await conn.execute(
                        text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{tbl}')")
                    )
                    assert result.scalar() is True, f"Tabla {tbl} no existe"
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_usuarios_has_auth_columns(self):
        """GREEN: usuarios tiene password_hash e is_2fa_enabled."""
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
                    text("SELECT column_name FROM information_schema.columns WHERE table_name = 'usuarios' AND column_name IN ('password_hash', 'is_2fa_enabled')")
                )
                cols = [r[0] for r in result.fetchall()]
                assert "password_hash" in cols
                assert "is_2fa_enabled" in cols
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_refresh_tokens_has_tenant_id(self):
        """TRIANGULATE: refresh_tokens tiene tenant_id."""
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
                    text("SELECT column_name FROM information_schema.columns WHERE table_name = 'refresh_tokens' AND column_name = 'tenant_id'")
                )
                assert result.scalar() == "tenant_id"
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_rate_limit_buckets_no_tenant_id(self):
        """TRIANGULATE: rate_limit_buckets NO tiene tenant_id (global)."""
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
                    text("SELECT column_name FROM information_schema.columns WHERE table_name = 'rate_limit_buckets' AND column_name = 'tenant_id'")
                )
                assert result.scalar() is None
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_downgrade_removes_c03_tables(self):
        """TRIANGULATE: downgrade a 001 remueve tablas C-03."""
        from alembic import command
        from alembic.config import Config

        _reset_database()
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
        command.upgrade(alembic_cfg, "head")
        command.downgrade(alembic_cfg, "001_tenant")

        test_engine = create_async_engine(settings.database_url, echo=False)
        async def check():
            async with test_engine.connect() as conn:
                for tbl in ["refresh_tokens", "password_reset_tokens", "two_factor_enrollments", "rate_limit_buckets"]:
                    result = await conn.execute(
                        text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{tbl}')")
                    )
                    assert result.scalar() is False, f"Tabla {tbl} debería haber sido eliminada"
                # tenants debe seguir existiendo
                result = await conn.execute(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tenants')")
                )
                assert result.scalar() is True
        asyncio.run(check())
        test_engine.sync_engine.dispose()
