"""Tests TDD para PerfilService y router de perfil (C-20).

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


async def _login(async_client: AsyncClient, email: str, password: str) -> str:
    from app.core import security
    response = await async_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    if response.status_code != 200:
        return ""
    return response.json().get("access_token", "")


async def _assign_role(
    db_session: AsyncSession,
    usuario_id: str,
    tenant_id: str,
    rol_codigo: str,
) -> None:
    from sqlalchemy import text
    await db_session.execute(
        text(
            "INSERT INTO usuario_rol (id, tenant_id, usuario_id, rol_id, created_at, updated_at) "
            "SELECT gen_random_uuid(), :tid, :uid, r.id, NOW(), NOW() "
            "FROM roles r WHERE r.tenant_id = :tid AND r.codigo = :rol "
            "LIMIT 1"
        ),
        {"tid": str(tenant_id), "uid": str(usuario_id), "rol": rol_codigo},
    )
    await db_session.commit()


# ============================================================
# GRUPO 1: PerfilService
# ============================================================


class TestPerfilService:
    """T-14: PerfilService self-service y PII."""

    @pytest.mark.asyncio
    async def test_perfil_service_edita_campos(self, db_session: AsyncSession, default_tenant):
        """RED: editar perfil actualiza campos permitidos."""
        from app.services.perfil_service import PerfilService

        user = await _create_user(db_session, default_tenant.id, "perfil.edit@test.com")
        svc = PerfilService(db_session, default_tenant.id, user.id)
        updated = await svc.editar_perfil({"nombre": "NuevoNombre", "banco": "Santander"})
        assert updated.nombre == "NuevoNombre"
        assert updated.banco == "Santander"

    @pytest.mark.asyncio
    async def test_perfil_service_404_usuario_eliminado(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: usuario soft-deleted → 404."""
        from app.services.perfil_service import PerfilService

        user = await _create_user(db_session, default_tenant.id, "perfil.del@test.com")
        from app.repositories.usuarios import UsuarioRepository
        repo = UsuarioRepository(db_session, default_tenant.id)
        await repo.soft_delete(user.id)

        svc = PerfilService(db_session, default_tenant.id, user.id)
        with pytest.raises(HTTPException) as exc_info:
            await svc.editar_perfil({"nombre": "X"})
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_perfil_service_pii_encrypted_roundtrip(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: cbu y email se cifran y descifran transparentemente."""
        from app.services.perfil_service import PerfilService

        user = await _create_user(db_session, default_tenant.id, "perfil.pii@test.com")
        svc = PerfilService(db_session, default_tenant.id, user.id)
        updated = await svc.editar_perfil({"cbu": "1234567890123456789012", "email": "nuevo@mail.com"})
        assert updated.cbu == "1234567890123456789012"
        assert updated.email == "nuevo@mail.com"

    @pytest.mark.asyncio
    async def test_perfil_service_rechaza_cuil(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: schema rechaza cuil (no es un test de service, sino de schema)."""
        from pydantic import ValidationError
        from app.schemas.perfil import PerfilUpdate
        with pytest.raises(ValidationError) as exc_info:
            PerfilUpdate(cuil="20-12345678-9")
        assert "cuil" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_perfil_service_tenant_isolation(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: no puede editar usuario de otro tenant."""
        from app.models.tenant import Tenant
        from app.services.perfil_service import PerfilService

        tenant_b = Tenant(nombre="TenantB", slug=f"tb-{uuid4().hex[:8]}", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        user_b = await _create_user(db_session, tenant_b.id, "perfil.iso@test.com")
        svc_a = PerfilService(db_session, default_tenant.id, user_b.id)
        with pytest.raises(HTTPException) as exc_info:
            await svc_a.editar_perfil({"nombre": "X"})
        assert exc_info.value.status_code == 404


# ============================================================
# GRUPO 2: Router PATCH /api/v1/perfil
# ============================================================


class TestPerfilRouter:
    """T-14: Integration tests for PATCH /api/v1/perfil."""

    @pytest.mark.asyncio
    async def test_perfil_endpoint_existe(self, async_client: AsyncClient):
        """Router registrado → no 404."""
        response = await async_client.patch("/api/v1/perfil", json={})
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_perfil_patch_sin_token_401(self, async_client: AsyncClient):
        """Sin JWT → 401."""
        response = await async_client.patch(
            "/api/v1/perfil",
            json={"nombre": "X"},
        )
        assert response.status_code == 401
