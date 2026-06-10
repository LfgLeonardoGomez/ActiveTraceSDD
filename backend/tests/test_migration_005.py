"""Tests TDD — migración 005 carrera_cohorte_materia (C-06).

Verifica:
- upgrade crea tablas carreras, cohortes y materias
- índices únicos parciales existen
- downgrade elimina las tablas limpiamente
"""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings

settings = Settings()


def _reset_database() -> None:
    async def _reset() -> None:
        engine = create_async_engine(settings.database_url, echo=False)
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
        await engine.dispose()

    asyncio.run(_reset())


def _run_migration_to(revision: str) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, revision)


def _run_downgrade_to(revision: str) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.downgrade(cfg, revision)


class TestMigration005EstructuraAcademica:
    """RED/GREEN/TRIANGULATE para migración 005_carrera_cohorte_materia."""

    def test_upgrade_creates_carreras_table(self) -> None:
        """RED: upgrade head crea tabla carreras."""
        _reset_database()
        _run_migration_to("head")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT FROM information_schema.tables "
                        "WHERE table_name = 'carreras'"
                        ")"
                    )
                )
                assert result.scalar() is True
            await engine.dispose()

        asyncio.run(check())

    def test_upgrade_creates_cohortes_table(self) -> None:
        """GREEN: upgrade head crea tabla cohortes."""
        _reset_database()
        _run_migration_to("head")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT FROM information_schema.tables "
                        "WHERE table_name = 'cohortes'"
                        ")"
                    )
                )
                assert result.scalar() is True
            await engine.dispose()

        asyncio.run(check())

    def test_upgrade_creates_materias_table(self) -> None:
        """GREEN: upgrade head crea tabla materias."""
        _reset_database()
        _run_migration_to("head")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT FROM information_schema.tables "
                        "WHERE table_name = 'materias'"
                        ")"
                    )
                )
                assert result.scalar() is True
            await engine.dispose()

        asyncio.run(check())

    def test_unique_index_carreras_exists(self) -> None:
        """TRIANGULATE: índice único parcial en carreras existe."""
        _reset_database()
        _run_migration_to("head")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT FROM pg_indexes "
                        "WHERE tablename = 'carreras' "
                        "AND indexname = 'idx_carreras_tenant_codigo'"
                        ")"
                    )
                )
                assert result.scalar() is True
            await engine.dispose()

        asyncio.run(check())

    def test_unique_index_cohortes_exists(self) -> None:
        """TRIANGULATE: índice único parcial en cohortes existe."""
        _reset_database()
        _run_migration_to("head")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT FROM pg_indexes "
                        "WHERE tablename = 'cohortes' "
                        "AND indexname = 'idx_cohortes_tenant_carrera_nombre'"
                        ")"
                    )
                )
                assert result.scalar() is True
            await engine.dispose()

        asyncio.run(check())

    def test_downgrade_removes_tables(self) -> None:
        """TRIANGULATE: downgrade a 004_audit_log elimina las tres tablas."""
        _reset_database()
        _run_migration_to("head")
        _run_downgrade_to("004_audit_log")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                for table in ("carreras", "cohortes", "materias"):
                    result = await conn.execute(
                        text(
                            f"SELECT EXISTS ("
                            f"SELECT FROM information_schema.tables "
                            f"WHERE table_name = '{table}'"
                            f")"
                        )
                    )
                    assert result.scalar() is False, f"Tabla {table} debe no existir tras downgrade"
            await engine.dispose()

        asyncio.run(check())
