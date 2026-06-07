"""Tests de TDD para migración Alembic 002 — C-04 RBAC.

Verifica que las tablas de RBAC existan, tengan columnas requeridas,
y que el seed de roles/permisos/matriz se cargue correctamente.
"""

import asyncio
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings

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


class TestMigration002:
    """Tests de migración C-04 (002_create_rbac_tables)."""

    def test_002_adds_codigo_to_roles(self):
        """RED: upgrade head agrega columna codigo a roles."""
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
                    text("SELECT column_name FROM information_schema.columns WHERE table_name = 'roles' AND column_name = 'codigo'")
                )
                assert result.scalar() == "codigo"
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_002_adds_codigo_to_permisos(self):
        """GREEN: upgrade head agrega columna codigo a permisos."""
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
                    text("SELECT column_name FROM information_schema.columns WHERE table_name = 'permisos' AND column_name = 'codigo'")
                )
                assert result.scalar() == "codigo"
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_002_creates_rol_permiso_table(self):
        """GREEN: upgrade head crea tabla rol_permiso."""
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
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'rol_permiso')")
                )
                assert result.scalar() is True
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_002_index_tenant_id_codigo_exists(self):
        """TRIANGULATE: índice compuesto (tenant_id, codigo) en roles y permisos."""
        from alembic import command
        from alembic.config import Config

        _reset_database()
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
        command.upgrade(alembic_cfg, "head")

        test_engine = create_async_engine(settings.database_url, echo=False)
        async def check():
            async with test_engine.connect() as conn:
                for tbl in ["roles", "permisos"]:
                    result = await conn.execute(
                        text(
                            f"SELECT indexname FROM pg_indexes WHERE tablename = '{tbl}' "
                            f"AND indexdef LIKE '%(tenant_id, codigo)%'"
                        )
                    )
                    row = result.fetchone()
                    assert row is not None, f"Falta índice (tenant_id, codigo) en {tbl}"
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_002_seeds_domain_roles(self):
        """TRIANGULATE: seed de 7 roles del dominio."""
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
                    text("SELECT codigo FROM roles WHERE deleted_at IS NULL ORDER BY codigo")
                )
                codes = [r[0] for r in result.fetchall()]
                expected = ["ADMIN", "ALUMNO", "COORDINADOR", "FINANZAS", "NEXO", "PROFESOR", "TUTOR"]
                assert codes == expected
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_002_seeds_permissions(self):
        """TRIANGULATE: seed de permisos base."""
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
                    text("SELECT COUNT(*) FROM permisos WHERE deleted_at IS NULL")
                )
                assert result.scalar() > 0
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_002_seeds_rol_permiso_matrix(self):
        """TRIANGULATE: seed de matriz rol_permiso."""
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
                    text("SELECT COUNT(*) FROM rol_permiso WHERE deleted_at IS NULL")
                )
                count = result.scalar()
                assert count > 0
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_002_nexo_has_no_permissions(self):
        """TRIANGULATE: rol NEXO tiene matriz vacía."""
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
                    text(
                        "SELECT COUNT(rp.id) FROM rol_permiso rp "
                        "JOIN roles r ON r.id = rp.rol_id WHERE r.codigo = 'NEXO'"
                    )
                )
                assert result.scalar() == 0
        asyncio.run(check())
        test_engine.sync_engine.dispose()

    def test_002_downgrade_removes_rbac_changes(self):
        """TRIANGULATE: downgrade a C-03 revierte cambios de RBAC."""
        from alembic import command
        from alembic.config import Config

        _reset_database()
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
        command.upgrade(alembic_cfg, "head")
        command.downgrade(alembic_cfg, "3a51a71a68ef")

        test_engine = create_async_engine(settings.database_url, echo=False)
        async def check():
            async with test_engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'rol_permiso')")
                )
                assert result.scalar() is False
        asyncio.run(check())
        test_engine.sync_engine.dispose()
