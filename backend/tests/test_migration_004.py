"""Tests TDD — migración 004 audit_log (C-05).

Verifica:
- upgrade crea tabla audit_log y trigger trg_audit_log_immutable
- INSERT funciona correctamente
- UPDATE lanza excepción "audit_log is immutable"
- DELETE lanza excepción "audit_log is immutable"
- downgrade elimina trigger, función y tabla
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


class TestMigration004AuditLog:
    """RED/GREEN/TRIANGULATE para migración 004_audit_log."""

    def test_upgrade_creates_audit_log_table(self) -> None:
        """RED: upgrade head crea tabla audit_log."""
        _reset_database()
        _run_migration_to("head")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT FROM information_schema.tables "
                        "WHERE table_name = 'audit_log'"
                        ")"
                    )
                )
                assert result.scalar() is True
            await engine.dispose()

        asyncio.run(check())

    def test_upgrade_creates_immutability_trigger(self) -> None:
        """GREEN: el trigger trg_audit_log_immutable existe tras upgrade."""
        _reset_database()
        _run_migration_to("head")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT FROM information_schema.triggers "
                        "WHERE trigger_name = 'trg_audit_log_immutable' "
                        "AND event_object_table = 'audit_log'"
                        ")"
                    )
                )
                assert result.scalar() is True
            await engine.dispose()

        asyncio.run(check())

    def test_insert_succeeds(self) -> None:
        """GREEN: INSERT en audit_log funciona correctamente."""
        _reset_database()
        _run_migration_to("head")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.begin() as conn:
                # Obtener tenant y usuario del seed
                tenant_row = await conn.execute(
                    text("SELECT id FROM tenants WHERE slug = 'default' LIMIT 1")
                )
                tenant_id = tenant_row.scalar()
                assert tenant_id is not None

                user_row = await conn.execute(
                    text("SELECT id FROM usuarios WHERE tenant_id = :tid LIMIT 1"),
                    {"tid": tenant_id},
                )
                user_id = user_row.scalar()
                assert user_id is not None

                await conn.execute(
                    text(
                        "INSERT INTO audit_log "
                        "(id, tenant_id, fecha_hora, actor_id, accion, filas_afectadas) "
                        "VALUES (gen_random_uuid(), :tid, NOW(), :uid, 'TEST_ACTION', 1)"
                    ),
                    {"tid": tenant_id, "uid": user_id},
                )
                count = await conn.execute(
                    text("SELECT COUNT(*) FROM audit_log")
                )
                assert count.scalar() == 1
            await engine.dispose()

        asyncio.run(check())

    def test_update_raises_immutable_exception(self) -> None:
        """TRIANGULATE: UPDATE sobre audit_log lanza excepción 'audit_log is immutable'."""
        _reset_database()
        _run_migration_to("head")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            # Insertar registro
            async with engine.begin() as conn:
                tenant_row = await conn.execute(
                    text("SELECT id FROM tenants WHERE slug = 'default' LIMIT 1")
                )
                tenant_id = tenant_row.scalar()
                user_row = await conn.execute(
                    text("SELECT id FROM usuarios WHERE tenant_id = :tid LIMIT 1"),
                    {"tid": tenant_id},
                )
                user_id = user_row.scalar()
                await conn.execute(
                    text(
                        "INSERT INTO audit_log "
                        "(id, tenant_id, fecha_hora, actor_id, accion, filas_afectadas) "
                        "VALUES (gen_random_uuid(), :tid, NOW(), :uid, 'TEST_ACTION', 0)"
                    ),
                    {"tid": tenant_id, "uid": user_id},
                )

            # Intentar UPDATE — debe lanzar excepción
            async with engine.begin() as conn:
                with pytest.raises(Exception, match="audit_log is immutable"):
                    await conn.execute(
                        text("UPDATE audit_log SET accion = 'MODIFIED'")
                    )
            await engine.dispose()

        asyncio.run(check())

    def test_delete_raises_immutable_exception(self) -> None:
        """TRIANGULATE: DELETE sobre audit_log lanza excepción 'audit_log is immutable'."""
        _reset_database()
        _run_migration_to("head")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.begin() as conn:
                tenant_row = await conn.execute(
                    text("SELECT id FROM tenants WHERE slug = 'default' LIMIT 1")
                )
                tenant_id = tenant_row.scalar()
                user_row = await conn.execute(
                    text("SELECT id FROM usuarios WHERE tenant_id = :tid LIMIT 1"),
                    {"tid": tenant_id},
                )
                user_id = user_row.scalar()
                await conn.execute(
                    text(
                        "INSERT INTO audit_log "
                        "(id, tenant_id, fecha_hora, actor_id, accion, filas_afectadas) "
                        "VALUES (gen_random_uuid(), :tid, NOW(), :uid, 'TEST_ACTION', 0)"
                    ),
                    {"tid": tenant_id, "uid": user_id},
                )

            async with engine.begin() as conn:
                with pytest.raises(Exception, match="audit_log is immutable"):
                    await conn.execute(text("DELETE FROM audit_log"))
            await engine.dispose()

        asyncio.run(check())

    def test_downgrade_removes_table_and_trigger(self) -> None:
        """TRIANGULATE: downgrade a 002_rbac elimina tabla y trigger."""
        _reset_database()
        _run_migration_to("head")
        _run_downgrade_to("002_rbac")

        async def check() -> None:
            engine = create_async_engine(settings.database_url, echo=False)
            async with engine.connect() as conn:
                table_exists = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT FROM information_schema.tables "
                        "WHERE table_name = 'audit_log'"
                        ")"
                    )
                )
                assert table_exists.scalar() is False

                trigger_exists = await conn.execute(
                    text(
                        "SELECT EXISTS ("
                        "SELECT FROM information_schema.triggers "
                        "WHERE trigger_name = 'trg_audit_log_immutable'"
                        ")"
                    )
                )
                assert trigger_exists.scalar() is False
            await engine.dispose()

        asyncio.run(check())
