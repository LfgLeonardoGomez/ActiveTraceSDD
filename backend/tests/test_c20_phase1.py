"""Tests Phase 1 — Foundation: Mensaje model, import, migration (C-20)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4


class TestMensajeModel:
    """T-01 RED → GREEN: Mensaje model exists and can be instantiated."""

    @pytest.mark.asyncio
    async def test_mensaje_model_import(self):
        """RED: app.models.mensaje must be importable."""
        from app.models.mensaje import Mensaje
        assert Mensaje is not None

    @pytest.mark.asyncio
    async def test_mensaje_model_columns(self, db_session: AsyncSession, default_tenant):
        """GREEN: Mensaje can be created with all required fields."""
        from app.models.mensaje import Mensaje
        from app.models.user import Usuario
        from app.repositories.usuarios import UsuarioRepository

        repo = UsuarioRepository(db_session, default_tenant.id)
        sender = await repo.create(nombre="Rem", apellidos="Itente", email="rem@test.com", estado="Activo")
        recipient = await repo.create(nombre="Des", apellidos="Tinatario", email="des@test.com", estado="Activo")

        msg = Mensaje(
            tenant_id=default_tenant.id,
            remitente_id=sender.id,
            destinatario_id=recipient.id,
            asunto="Hola",
            cuerpo="Cuerpo del mensaje",
        )
        db_session.add(msg)
        await db_session.commit()
        await db_session.refresh(msg)

        assert msg.id is not None
        assert msg.tenant_id == default_tenant.id
        assert msg.remitente_id == sender.id
        assert msg.destinatario_id == recipient.id
        assert msg.asunto == "Hola"
        assert msg.cuerpo == "Cuerpo del mensaje"
        assert msg.parent_id is None
        assert msg.created_at is not None

    @pytest.mark.asyncio
    async def test_mensaje_reply_self_fk(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: reply with parent_id works."""
        from app.models.mensaje import Mensaje
        from app.repositories.usuarios import UsuarioRepository

        repo = UsuarioRepository(db_session, default_tenant.id)
        sender = await repo.create(nombre="Rem2", apellidos="Itente", email="rem2@test.com", estado="Activo")
        recipient = await repo.create(nombre="Des2", apellidos="Tinatario", email="des2@test.com", estado="Activo")

        root = Mensaje(
            tenant_id=default_tenant.id,
            remitente_id=sender.id,
            destinatario_id=recipient.id,
            asunto="Root",
            cuerpo="Root body",
        )
        db_session.add(root)
        await db_session.commit()
        await db_session.refresh(root)

        reply = Mensaje(
            tenant_id=default_tenant.id,
            remitente_id=recipient.id,
            destinatario_id=sender.id,
            asunto="Re: Root",
            cuerpo="Reply body",
            parent_id=root.id,
        )
        db_session.add(reply)
        await db_session.commit()
        await db_session.refresh(reply)

        assert reply.parent_id == root.id


class TestMensajeModelRegistered:
    """T-02: Mensaje is exported from app.models."""

    @pytest.mark.asyncio
    async def test_mensaje_in_all(self):
        from app.models import __all__
        assert "Mensaje" in __all__


class TestMigration016:
    """T-03: Migration 016 exists and can be imported."""

    @pytest.mark.asyncio
    async def test_migration_016_exists(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "migration_016",
            "alembic/versions/016_c20_mensaje_perfil.py",
        )
        assert spec is not None
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        assert migration.revision == "016_c20_mensaje_perfil"
        assert migration.down_revision == "015_c18_liquidaciones"
