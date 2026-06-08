"""Tests TDD — Endpoints de impersonación (C-05).

Verifica:
- POST /api/auth/impersonate exitoso → 200 + token con claims imp=True
- POST sin permiso → 403
- POST con target de otro tenant → 404
- POST con target inactivo → 400
- DELETE con token de impersonación → 204 + audit IMPERSONACION_FINALIZAR
- DELETE con token normal → 400
- AuditLog IMPERSONACION_INICIAR tiene actor correcto
- AuditLog IMPERSONACION_FINALIZAR registrado correctamente
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core import security
from app.models.audit_log import AuditLog
from app.models.tenant import Tenant
from app.models.user import Usuario
from app.repositories.rbac_repository import (
    PermisoRepository,
    RolPermiso,
    RolPermisoRepository,
    RolRepository,
)


async def _create_user(
    db_session: AsyncSession,
    tenant_id,
    email: str,
    estado: str = "Activo",
) -> Usuario:
    user = Usuario(
        nombre="Test",
        apellidos="User",
        email=email,
        estado=estado,
        tenant_id=tenant_id,
        password_hash=security.hash_password("Pass1234"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _setup_impersonation_permission(
    db_session: AsyncSession,
    tenant_id,
    rol_codigo: str = "ADMIN_IMP",
) -> None:
    """Crea rol con permiso impersonacion:usar en el tenant."""
    rol_repo = RolRepository(db_session, tenant_id)
    perm_repo = PermisoRepository(db_session, tenant_id)
    rp_repo = RolPermisoRepository(db_session, tenant_id)

    rol = await rol_repo.create(codigo=rol_codigo, nombre="Admin Impersonation")
    perm = await perm_repo.create(
        codigo="impersonacion:usar",
        nombre="Usar impersonación",
    )
    await rp_repo.create(rol_id=rol.id, permiso_id=perm.id, es_propio=False)


class TestStartImpersonation:
    """Tests para POST /api/auth/impersonate."""

    @pytest.mark.asyncio
    async def test_impersonate_success(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED: actor con permiso impersonacion:usar obtiene token de impersonación."""
        await _setup_impersonation_permission(db_session, default_tenant.id)

        actor = await _create_user(db_session, default_tenant.id, "actor@test.com")
        target = await _create_user(db_session, default_tenant.id, "target@test.com")

        actor_token = security.create_access_token(
            user_id=actor.id,
            tenant_id=default_tenant.id,
            roles=["ADMIN_IMP"],
        )

        response = await async_client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target.id)},
            headers={"Authorization": f"Bearer {actor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

        payload = security.verify_access_token(data["access_token"])
        assert payload is not None
        assert payload["imp"] is True
        assert payload["act"] == str(actor.id)
        assert payload["sub"] == str(target.id)

    @pytest.mark.asyncio
    async def test_impersonate_without_permission_returns_403(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN: sin permiso impersonacion:usar → 403."""
        from app.repositories.rbac_repository import RolRepository

        rol_repo = RolRepository(db_session, default_tenant.id)
        await rol_repo.create(codigo="NOPERM", nombre="Sin Permisos")

        actor = await _create_user(db_session, default_tenant.id, "noperm@test.com")
        target = await _create_user(db_session, default_tenant.id, "target2@test.com")

        actor_token = security.create_access_token(
            user_id=actor.id,
            tenant_id=default_tenant.id,
            roles=["NOPERM"],
        )

        response = await async_client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target.id)},
            headers={"Authorization": f"Bearer {actor_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_impersonate_target_other_tenant_returns_404(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: target de otro tenant → 404."""
        await _setup_impersonation_permission(db_session, default_tenant.id, "ADMIN_IMP2")

        actor = await _create_user(db_session, default_tenant.id, "actor2@test.com")
        actor_token = security.create_access_token(
            user_id=actor.id,
            tenant_id=default_tenant.id,
            roles=["ADMIN_IMP2"],
        )

        # Crear tenant B y usuario en él
        tenant_b = Tenant(nombre="Tenant B", slug="tenant-b-imp", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        other_user = await _create_user(db_session, tenant_b.id, "other@test.com")

        response = await async_client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(other_user.id)},
            headers={"Authorization": f"Bearer {actor_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_impersonate_inactive_target_returns_400(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: target inactivo → 400."""
        await _setup_impersonation_permission(db_session, default_tenant.id, "ADMIN_IMP3")

        actor = await _create_user(db_session, default_tenant.id, "actor3@test.com")
        inactive_target = await _create_user(
            db_session, default_tenant.id, "inactive@test.com", estado="Inactivo"
        )
        actor_token = security.create_access_token(
            user_id=actor.id,
            tenant_id=default_tenant.id,
            roles=["ADMIN_IMP3"],
        )

        response = await async_client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(inactive_target.id)},
            headers={"Authorization": f"Bearer {actor_token}"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_impersonate_creates_audit_log(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: POST exitoso crea AuditLog IMPERSONACION_INICIAR con actor real."""
        await _setup_impersonation_permission(db_session, default_tenant.id, "ADMIN_IMP4")

        actor = await _create_user(db_session, default_tenant.id, "actor4@test.com")
        target = await _create_user(db_session, default_tenant.id, "target4@test.com")
        actor_token = security.create_access_token(
            user_id=actor.id,
            tenant_id=default_tenant.id,
            roles=["ADMIN_IMP4"],
        )

        response = await async_client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target.id)},
            headers={"Authorization": f"Bearer {actor_token}"},
        )
        assert response.status_code == 200

        result = await db_session.execute(
            select(AuditLog).where(
                AuditLog.tenant_id == default_tenant.id,
                AuditLog.accion == "IMPERSONACION_INICIAR",
            )
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.actor_id == actor.id
        assert log.impersonado_id == target.id


class TestEndImpersonation:
    """Tests para DELETE /api/auth/impersonate."""

    @pytest.mark.asyncio
    async def test_end_impersonation_success(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED: DELETE con token de impersonación → 204 + AuditLog FINALIZAR."""
        actor = await _create_user(db_session, default_tenant.id, "endactor@test.com")
        target = await _create_user(db_session, default_tenant.id, "endtarget@test.com")

        imp_token = security.create_impersonation_token(
            actor_id=actor.id,
            target_id=target.id,
            tenant_id=default_tenant.id,
            roles=[],
        )

        response = await async_client.delete(
            "/api/auth/impersonate",
            headers={"Authorization": f"Bearer {imp_token}"},
        )
        assert response.status_code == 204

        result = await db_session.execute(
            select(AuditLog).where(
                AuditLog.accion == "IMPERSONACION_FINALIZAR",
                AuditLog.tenant_id == default_tenant.id,
            )
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.actor_id == actor.id
        assert log.impersonado_id == target.id

    @pytest.mark.asyncio
    async def test_end_impersonation_with_normal_token_returns_400(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN: DELETE con token normal (no impersonación) → 400."""
        user = await _create_user(db_session, default_tenant.id, "normalend@test.com")
        normal_token = security.create_access_token(
            user_id=user.id,
            tenant_id=default_tenant.id,
            roles=[],
        )

        response = await async_client.delete(
            "/api/auth/impersonate",
            headers={"Authorization": f"Bearer {normal_token}"},
        )
        assert response.status_code == 400
