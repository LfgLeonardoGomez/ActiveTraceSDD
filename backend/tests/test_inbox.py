"""Tests TDD para MensajeService y router de inbox (C-20).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Tests usan DB real (sin mocks — regla dura).
"""

import pytest
from uuid import uuid4

from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================
# Helpers
# ============================================================


async def _create_user(
    db_session: AsyncSession,
    tenant_id: str,
    email: str,
    nombre: str = "Test",
    apellidos: str = "User",
) -> None:
    from app.repositories.usuarios import UsuarioRepository
    repo = UsuarioRepository(db_session, tenant_id)
    return await repo.create(
        nombre=nombre,
        apellidos=apellidos,
        email=email,
        estado="Activo",
    )


async def _create_message(
    db_session: AsyncSession,
    tenant_id: str,
    remitente_id: str,
    destinatario_id: str,
    asunto: str,
    cuerpo: str,
    parent_id: str | None = None,
) -> None:
    from app.models.mensaje import Mensaje
    msg = Mensaje(
        tenant_id=tenant_id,
        remitente_id=remitente_id,
        destinatario_id=destinatario_id,
        asunto=asunto,
        cuerpo=cuerpo,
        parent_id=parent_id,
    )
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)
    return msg


# ============================================================
# GRUPO 1: MensajeService
# ============================================================


class TestMensajeService:
    """T-15: MensajeService thread access, replies, tenant isolation."""

    @pytest.mark.asyncio
    async def test_mensaje_service_list_inbox(self, db_session: AsyncSession, default_tenant):
        """RED: list_inbox retorna roots donde user es destinatario."""
        from app.services.mensaje_service import MensajeService

        sender = await _create_user(db_session, default_tenant.id, "sender.list@test.com")
        recipient = await _create_user(db_session, default_tenant.id, "recipient.list@test.com")
        root = await _create_message(db_session, default_tenant.id, sender.id, recipient.id, "Asunto", "Cuerpo")

        svc = MensajeService(db_session, default_tenant.id, recipient.id)
        items = await svc.list_inbox(recipient.id)
        assert len(items) == 1
        assert items[0].id == root.id

    @pytest.mark.asyncio
    async def test_mensaje_service_empty_inbox(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: inbox vacío → lista vacía."""
        from app.services.mensaje_service import MensajeService

        user = await _create_user(db_session, default_tenant.id, "empty@test.com")
        svc = MensajeService(db_session, default_tenant.id, user.id)
        items = await svc.list_inbox(user.id)
        assert items == []

    @pytest.mark.asyncio
    async def test_mensaje_service_get_thread_ok(self, db_session: AsyncSession, default_tenant):
        """GREEN: get_thread retorna root + replies."""
        from app.services.mensaje_service import MensajeService

        sender = await _create_user(db_session, default_tenant.id, "sender.thread@test.com")
        recipient = await _create_user(db_session, default_tenant.id, "recipient.thread@test.com")
        root = await _create_message(db_session, default_tenant.id, sender.id, recipient.id, "Root", "Root body")
        reply = await _create_message(db_session, default_tenant.id, recipient.id, sender.id, "Re", "Reply body", parent_id=root.id)

        svc = MensajeService(db_session, default_tenant.id, recipient.id)
        r, replies = await svc.get_thread(root.id, recipient.id)
        assert r.id == root.id
        assert len(replies) == 1
        assert replies[0].id == reply.id

    @pytest.mark.asyncio
    async def test_mensaje_service_get_thread_403_no_participante(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: usuario no participante → 403."""
        from app.services.mensaje_service import MensajeService

        sender = await _create_user(db_session, default_tenant.id, "sender.403@test.com")
        recipient = await _create_user(db_session, default_tenant.id, "recipient.403@test.com")
        outsider = await _create_user(db_session, default_tenant.id, "outsider.403@test.com")
        root = await _create_message(db_session, default_tenant.id, sender.id, recipient.id, "Root", "Root body")

        svc = MensajeService(db_session, default_tenant.id, outsider.id)
        with pytest.raises(HTTPException) as exc_info:
            await svc.get_thread(root.id, outsider.id)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_mensaje_service_responder_crea_reply(self, db_session: AsyncSession, default_tenant):
        """GREEN: responder crea reply con parent_id."""
        from app.services.mensaje_service import MensajeService

        sender = await _create_user(db_session, default_tenant.id, "sender.reply@test.com")
        recipient = await _create_user(db_session, default_tenant.id, "recipient.reply@test.com")
        root = await _create_message(db_session, default_tenant.id, sender.id, recipient.id, "Root", "Root body")

        svc = MensajeService(db_session, default_tenant.id, recipient.id)
        reply = await svc.responder(root.id, {"cuerpo": "Nueva respuesta"})
        assert reply.parent_id == root.id
        assert reply.cuerpo == "Nueva respuesta"

    @pytest.mark.asyncio
    async def test_mensaje_service_responder_404_thread_inexistente(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: responder a thread inexistente → 404."""
        from app.services.mensaje_service import MensajeService

        user = await _create_user(db_session, default_tenant.id, "user.404@test.com")
        svc = MensajeService(db_session, default_tenant.id, user.id)
        with pytest.raises(HTTPException) as exc_info:
            await svc.responder(uuid4(), {"cuerpo": "X"})
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_mensaje_service_tenant_isolation(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: thread de otro tenant → 404."""
        from app.models.tenant import Tenant
        from app.services.mensaje_service import MensajeService

        tenant_b = Tenant(nombre="TenantB", slug=f"tb-{uuid4().hex[:8]}", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        sender = await _create_user(db_session, default_tenant.id, "sender.iso@test.com")
        recipient = await _create_user(db_session, default_tenant.id, "recipient.iso@test.com")
        root = await _create_message(db_session, default_tenant.id, sender.id, recipient.id, "Root", "Root body")

        svc_b = MensajeService(db_session, tenant_b.id, recipient.id)
        with pytest.raises(HTTPException) as exc_info:
            await svc_b.get_thread(root.id, recipient.id)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_mensaje_service_soft_delete_oculta(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: mensaje soft-deleted no aparece en inbox."""
        from app.services.mensaje_service import MensajeService
        from app.repositories.mensaje_repository import MensajeRepository

        sender = await _create_user(db_session, default_tenant.id, "sender.sd@test.com")
        recipient = await _create_user(db_session, default_tenant.id, "recipient.sd@test.com")
        root = await _create_message(db_session, default_tenant.id, sender.id, recipient.id, "Root", "Root body")

        repo = MensajeRepository(db_session, default_tenant.id)
        await repo.delete(root.id)

        svc = MensajeService(db_session, default_tenant.id, recipient.id)
        items = await svc.list_inbox(recipient.id)
        assert root.id not in [m.id for m in items]


# ============================================================
# GRUPO 2: Router inbox
# ============================================================


class TestInboxRouter:
    """T-15: Integration tests for inbox router."""

    @pytest.mark.asyncio
    async def test_inbox_endpoint_existe(self, async_client: AsyncClient):
        """Router registrado → no 404."""
        response = await async_client.get("/api/v1/inbox")
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_inbox_get_sin_token_401(self, async_client: AsyncClient):
        """Sin JWT → 401."""
        response = await async_client.get("/api/v1/inbox")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_inbox_responder_sin_token_401(self, async_client: AsyncClient):
        """Sin JWT en responder → 401."""
        response = await async_client.post(
            f"/api/v1/inbox/{uuid4()}/responder",
            json={"cuerpo": "test"},
        )
        assert response.status_code == 401
