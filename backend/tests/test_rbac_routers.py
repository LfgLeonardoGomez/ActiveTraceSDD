"""Tests de integración para routers RBAC.

Verifica CRUD de roles, permisos y asignaciones protegido por require_permission.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core import security
from app.models.user import Usuario
from app.repositories.rbac_repository import (
    RolRepository,
    PermisoRepository,
    RolPermisoRepository,
)


async def _create_user_with_role(
    db_session: AsyncSession,
    tenant_id,
    email: str,
    role_codes: list[str],
) -> tuple[Usuario, str]:
    """Helper: crea usuario y emite access token con roles específicos."""
    user = Usuario(
        nombre="Test",
        apellidos="User",
        email=email,
        estado="activo",
        tenant_id=tenant_id,
        password_hash=security.hash_password("Pass1234"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = security.create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        roles=role_codes,
    )
    return user, token


class TestRolRouter:
    """Tests para /api/v1/roles."""

    @pytest.fixture
    async def admin_token(self, db_session: AsyncSession, default_tenant):
        """Token de usuario con rol ADMIN (que tiene permiso roles:gestionar)."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        admin_rol = await rol_repo.create(codigo="ADMIN", nombre="Administrador")
        perm = await perm_repo.create(codigo="roles:gestionar", nombre="Gestionar roles", modulo="roles")
        await rp_repo.create(rol_id=admin_rol.id, permiso_id=perm.id, es_propio=False)

        _, token = await _create_user_with_role(
            db_session, default_tenant.id, "admin@test.com", ["ADMIN"]
        )
        return token

    @pytest.fixture
    async def no_perms_token(self, db_session: AsyncSession, default_tenant):
        """Token de usuario sin permisos (rol NEXO)."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        # NEXO se crea sin permisos
        await rol_repo.create(codigo="NEXO", nombre="Nexo")

        _, token = await _create_user_with_role(
            db_session, default_tenant.id, "nexo@test.com", ["NEXO"]
        )
        return token

    @pytest.mark.asyncio
    async def test_list_roles(self, async_client: AsyncClient, admin_token):
        """RED: GET /api/v1/roles devuelve lista de roles."""
        resp = await async_client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_create_role(self, async_client: AsyncClient, admin_token):
        """GREEN: POST /api/v1/roles crea rol."""
        resp = await async_client.post(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"codigo": "SUPERVISOR", "nombre": "Supervisor", "descripcion": "Nuevo rol"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["codigo"] == "SUPERVISOR"

    @pytest.mark.asyncio
    async def test_update_role(self, async_client: AsyncClient, admin_token):
        """TRIANGULATE: PUT /api/v1/roles/{id} actualiza rol."""
        # Crear primero
        create_resp = await async_client.post(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"codigo": "UPD_R", "nombre": "Update Me"},
        )
        role_id = create_resp.json()["id"]

        resp = await async_client.put(
            f"/api/v1/roles/{role_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"nombre": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_role(self, async_client: AsyncClient, admin_token):
        """TRIANGULATE: DELETE /api/v1/roles/{id} soft delete."""
        create_resp = await async_client.post(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"codigo": "DEL_R", "nombre": "Delete Me"},
        )
        role_id = create_resp.json()["id"]

        resp = await async_client.delete(
            f"/api/v1/roles/{role_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_no_permission_returns_403(self, async_client: AsyncClient, no_perms_token):
        """TRIANGULATE: usuario sin roles:gestionar → 403."""
        resp = await async_client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {no_perms_token}"},
        )
        assert resp.status_code == 403


class TestPermisoRouter:
    """Tests para /api/v1/permisos."""

    @pytest.fixture
    async def admin_token(self, db_session: AsyncSession, default_tenant):
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        admin_rol = await rol_repo.create(codigo="ADMIN", nombre="Administrador")
        perm = await perm_repo.create(codigo="permisos:gestionar", nombre="Gestionar permisos", modulo="permisos")
        await rp_repo.create(rol_id=admin_rol.id, permiso_id=perm.id, es_propio=False)

        _, token = await _create_user_with_role(
            db_session, default_tenant.id, "adminp@test.com", ["ADMIN"]
        )
        return token

    @pytest.mark.asyncio
    async def test_list_permisos(self, async_client: AsyncClient, admin_token):
        """RED: GET /api/v1/permisos devuelve permisos."""
        resp = await async_client.get(
            "/api/v1/permisos",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_create_permiso(self, async_client: AsyncClient, admin_token):
        """GREEN: POST /api/v1/permisos crea permiso."""
        resp = await async_client.post(
            "/api/v1/permisos",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"codigo": "reportes:exportar", "nombre": "Exportar reportes", "modulo": "reportes"},
        )
        assert resp.status_code == 201
        assert resp.json()["codigo"] == "reportes:exportar"


class TestRolPermisoRouter:
    """Tests para /api/v1/rol-permisos."""

    @pytest.fixture
    async def admin_token(self, db_session: AsyncSession, default_tenant):
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        admin_rol = await rol_repo.create(codigo="ADMIN", nombre="Administrador")
        perm = await perm_repo.create(codigo="roles:gestionar", nombre="Gestionar roles", modulo="roles")
        await rp_repo.create(rol_id=admin_rol.id, permiso_id=perm.id, es_propio=False)

        _, token = await _create_user_with_role(
            db_session, default_tenant.id, "adminrp@test.com", ["ADMIN"]
        )
        return token

    @pytest.mark.asyncio
    async def test_assign_permiso_to_rol(self, async_client: AsyncClient, admin_token, db_session, default_tenant):
        """RED: POST /api/v1/rol-permisos asigna permiso a rol."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rol = await rol_repo.create(codigo="ASG_R", nombre="Asignar Rol")
        perm = await perm_repo.create(codigo="asg:p", nombre="Asignar P", modulo="asg")

        resp = await async_client.post(
            "/api/v1/rol-permisos",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"rol_id": str(rol.id), "permiso_id": str(perm.id), "es_propio": True},
        )
        assert resp.status_code == 201
        assert resp.json()["es_propio"] is True

    @pytest.mark.asyncio
    async def test_list_rol_permisos(self, async_client: AsyncClient, admin_token, db_session, default_tenant):
        """GREEN: GET /api/v1/roles/{rol_id}/permisos lista permisos de un rol."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        rol = await rol_repo.create(codigo="LST_R", nombre="List Rol")
        perm = await perm_repo.create(codigo="lst:p", nombre="List P", modulo="lst")
        await rp_repo.create(rol_id=rol.id, permiso_id=perm.id)

        resp = await async_client.get(
            f"/api/v1/roles/{rol.id}/permisos",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_remove_rol_permiso(self, async_client: AsyncClient, admin_token, db_session, default_tenant):
        """TRIANGULATE: DELETE /api/v1/rol-permisos/{id} quita asignación."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        rol = await rol_repo.create(codigo="REM_R", nombre="Remove Rol")
        perm = await perm_repo.create(codigo="rem:p", nombre="Remove P", modulo="rem")
        rp = await rp_repo.create(rol_id=rol.id, permiso_id=perm.id)

        resp = await async_client.delete(
            f"/api/v1/rol-permisos/{rp.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 204
