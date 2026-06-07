"""Tests de integración para require_permission (guard RBAC).

Verifica fail-closed, resolución server-side, propio y cambio inmediato.
"""

import pytest
from fastapi import HTTPException
from uuid import uuid4

from app.core.dependencies import CurrentUser, require_permission
from app.models.role import Rol, Permiso, RolPermiso
from app.repositories.rbac_repository import (
    RolRepository,
    PermisoRepository,
    RolPermisoRepository,
)
from app.schemas.rbac_schema import PermissionContext


class TestRequirePermission:
    """Tests para la dependency require_permission."""

    @pytest.fixture
    async def seed_guard(self, db_session, default_tenant):
        """Seed de rol y permiso para tests del guard."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        rol = await rol_repo.create(codigo="GUARD_R", nombre="Guard Rol")
        perm = await perm_repo.create(codigo="guard:action", nombre="Guard Action", modulo="guard")
        await rp_repo.create(rol_id=rol.id, permiso_id=perm.id, es_propio=True)

        return rol, perm

    @pytest.mark.asyncio
    async def test_user_with_permission_access(self, db_session, default_tenant, seed_guard):
        """RED: usuario con permiso → PermissionContext con has_permission=True."""
        rol, perm = seed_guard
        user = CurrentUser(
            id=uuid4(),
            tenant_id=default_tenant.id,
            email="test@test.com",
            roles=["GUARD_R"],
        )

        guard = require_permission("guard:action")
        ctx = await guard(current_user=user, db=db_session)

        assert isinstance(ctx, PermissionContext)
        assert ctx.has_permission is True
        assert ctx.is_propio is True
        assert "guard:action" in ctx.effective_permissions

    @pytest.mark.asyncio
    async def test_user_without_permission_403(self, db_session, default_tenant, seed_guard):
        """GREEN: usuario sin permiso → HTTPException 403."""
        user = CurrentUser(
            id=uuid4(),
            tenant_id=default_tenant.id,
            email="test@test.com",
            roles=["GUARD_R"],
        )

        guard = require_permission("guard:missing")
        with pytest.raises(HTTPException) as exc_info:
            await guard(current_user=user, db=db_session)

        assert exc_info.value.status_code == 403
        assert "denegado" in exc_info.value.detail.lower() or "permiso" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_matrix_change_reflected_immediately(self, db_session, default_tenant, seed_guard):
        """TRIANGULATE: cambio en matriz se refleja sin re-login."""
        rol, perm = seed_guard
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)

        # Crear un nuevo permiso y asignarlo
        new_perm = await perm_repo.create(codigo="guard:new", nombre="New Guard", modulo="guard")
        await rp_repo.create(rol_id=rol.id, permiso_id=new_perm.id)

        user = CurrentUser(
            id=uuid4(),
            tenant_id=default_tenant.id,
            email="test@test.com",
            roles=["GUARD_R"],
        )

        guard = require_permission("guard:new")
        ctx = await guard(current_user=user, db=db_session)

        assert ctx.has_permission is True
        assert "guard:new" in ctx.effective_permissions

    @pytest.mark.asyncio
    async def test_is_propio_false_when_global(self, db_session, default_tenant):
        """TRIANGULATE: permiso global → is_propio=False."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        rol = await rol_repo.create(codigo="GLOBAL_R", nombre="Global Rol")
        perm = await perm_repo.create(codigo="global:act", nombre="Global Act", modulo="global")
        await rp_repo.create(rol_id=rol.id, permiso_id=perm.id, es_propio=False)

        user = CurrentUser(
            id=uuid4(),
            tenant_id=default_tenant.id,
            email="test@test.com",
            roles=["GLOBAL_R"],
        )

        guard = require_permission("global:act")
        ctx = await guard(current_user=user, db=db_session)

        assert ctx.has_permission is True
        assert ctx.is_propio is False

    @pytest.mark.asyncio
    async def test_other_tenant_isolated(self, db_session, default_tenant, seed_guard):
        """TRIANGULATE: permisos de otro tenant no otorgan acceso."""
        user = CurrentUser(
            id=uuid4(),
            tenant_id=uuid4(),  # otro tenant
            email="test@test.com",
            roles=["GUARD_R"],
        )

        guard = require_permission("guard:action")
        with pytest.raises(HTTPException) as exc_info:
            await guard(current_user=user, db=db_session)

        assert exc_info.value.status_code == 403
