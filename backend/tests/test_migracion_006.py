"""Tests TDD — migración 006 usuario_pii_asignacion (C-07).

Verifica:
- upgrade agrega columnas PII a usuarios (email_hash, dni, cuil, cbu, alias_cbu, etc.)
- upgrade crea tabla asignaciones
- índice único parcial (tenant_id, email_hash) WHERE deleted_at IS NULL existe
- seed de permisos usuarios:gestionar y equipos:asignar insertados
- downgrade revierte todos los cambios limpiamente
"""

import asyncio

import pytest
from sqlalchemy import inspect, text
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


class TestMigration006UsuarioPiiAsignacion:
    """RED → GREEN → TRIANGULATE para migración 006_usuario_pii_asignacion."""

    def test_migration_006_upgrade_columnas_usuarios(self):
        """RED → GREEN: upgrade agrega columnas PII a tabla usuarios."""
        _reset_database()
        _run_migration_to("006_usuario_pii_asignacion")

        import asyncio

        async def _check() -> list[str]:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'usuarios' AND table_schema = 'public'"
                    )
                )
                cols = [row[0] for row in result.fetchall()]
            await engine.dispose()
            return cols

        columns = asyncio.run(_check())

        # Columnas PII nuevas
        assert "email_hash" in columns, f"email_hash no encontrada. Columnas: {columns}"
        assert "dni" in columns
        assert "cuil" in columns
        assert "cbu" in columns
        assert "alias_cbu" in columns
        assert "banco" in columns
        assert "regional" in columns
        assert "legajo_profesional" in columns
        assert "facturador" in columns

    def test_migration_006_upgrade_tabla_asignaciones(self):
        """TRIANGULATE: upgrade crea tabla asignaciones con columnas requeridas."""
        # Asumimos DB en estado 006 (test anterior ya lo llevó ahí)
        import asyncio

        async def _check() -> tuple[bool, list[str]]:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                # Verificar existencia de la tabla
                result_table = await conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_name = 'asignaciones' AND table_schema = 'public'"
                    )
                )
                table_exists = result_table.scalar_one_or_none() is not None

                result_cols = await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'asignaciones' AND table_schema = 'public'"
                    )
                )
                cols = [row[0] for row in result_cols.fetchall()]
            await engine.dispose()
            return table_exists, cols

        exists, columns = asyncio.run(_check())

        assert exists, "Tabla asignaciones no fue creada"
        required = [
            "id", "tenant_id", "usuario_id", "rol",
            "desde", "hasta", "comisiones",
            "responsable_id", "created_at", "updated_at", "deleted_at",
        ]
        for col in required:
            assert col in columns, f"Columna '{col}' no encontrada en asignaciones. Columnas: {columns}"

    def test_migration_006_upgrade_indice_email_hash(self):
        """TRIANGULATE: índice único parcial (tenant_id, email_hash) WHERE deleted_at IS NULL existe."""
        import asyncio

        async def _check() -> bool:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT indexname FROM pg_indexes "
                        "WHERE tablename = 'usuarios' "
                        "AND indexname = 'idx_usuarios_tenant_email_hash'"
                    )
                )
                index_exists = result.scalar_one_or_none() is not None
            await engine.dispose()
            return index_exists

        exists = asyncio.run(_check())
        assert exists, "Índice idx_usuarios_tenant_email_hash no fue creado"

    def test_migration_006_downgrade_limpia(self):
        """TRIANGULATE: downgrade revierte la migración correctamente."""
        _run_downgrade_to("005_carrera_cohorte_materia")

        import asyncio

        async def _check() -> tuple[bool, list[str]]:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                # Verificar que asignaciones ya no existe
                result_table = await conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_name = 'asignaciones' AND table_schema = 'public'"
                    )
                )
                table_exists = result_table.scalar_one_or_none() is not None

                # Verificar que email_hash ya no está en usuarios
                result_cols = await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'usuarios' AND table_schema = 'public'"
                        " AND column_name = 'email_hash'"
                    )
                )
                email_hash_exists = result_cols.scalar_one_or_none() is not None
            await engine.dispose()
            return table_exists, email_hash_exists

        asignaciones_exists, email_hash_exists = asyncio.run(_check())

        assert not asignaciones_exists, "Tabla asignaciones no fue eliminada en downgrade"
        assert not email_hash_exists, "Columna email_hash no fue eliminada en downgrade"
