"""Tests de TDD para repositories RBAC.

Verifica operaciones CRUD con scope de tenant y soft delete.
"""

import pytest
from uuid import uuid4

from app.models.role import Rol, Permiso, RolPermiso
from app.repositories.rbac_repository import (
    RolRepository,
    PermisoRepository,
    RolPermisoRepository,
)


class TestRolRepository:
    """Tests para RolRepository."""

    @pytest.mark.asyncio
    async def test_get_by_codigo(self, db_session, default_tenant):
        """RED: obtener rol por código dentro del tenant."""
        repo = RolRepository(db_session, default_tenant.id)
        rol = await repo.create(codigo="TEST_R", nombre="Test Rol")

        found = await repo.get_by_codigo("TEST_R")
        assert found is not None
        assert found.id == rol.id

    @pytest.mark.asyncio
    async def test_get_by_codigo_other_tenant_not_found(self, db_session, default_tenant):
        """GREEN: rol de otro tenant no se encuentra."""
        repo = RolRepository(db_session, default_tenant.id)
        await repo.create(codigo="OTHER_R", nombre="Other Rol")

        other_repo = RolRepository(db_session, uuid4())
        found = await other_repo.get_by_codigo("OTHER_R")
        assert found is None

    @pytest.mark.asyncio
    async def test_list_by_tenant_excludes_soft_deleted(self, db_session, default_tenant):
        """TRIANGULATE: soft delete excluye de listados."""
        repo = RolRepository(db_session, default_tenant.id)
        rol = await repo.create(codigo="DEL_R", nombre="Delete Me")
        await repo.delete(rol.id)

        roles = await repo.list()
        assert all(r.codigo != "DEL_R" for r in roles)

    @pytest.mark.asyncio
    async def test_soft_delete(self, db_session, default_tenant):
        """TRIANGULATE: soft delete marca deleted_at."""
        repo = RolRepository(db_session, default_tenant.id)
        rol = await repo.create(codigo="SOFT_R", nombre="Soft Delete")
        deleted = await repo.delete(rol.id)

        assert deleted is True
        assert rol.deleted_at is not None


class TestPermisoRepository:
    """Tests para PermisoRepository."""

    @pytest.mark.asyncio
    async def test_get_by_codigo(self, db_session, default_tenant):
        """RED: obtener permiso por código."""
        repo = PermisoRepository(db_session, default_tenant.id)
        permiso = await repo.create(
            codigo="test:accion",
            nombre="Test Accion",
            modulo="test",
        )

        found = await repo.get_by_codigo("test:accion")
        assert found is not None
        assert found.id == permiso.id

    @pytest.mark.asyncio
    async def test_list_by_tenant(self, db_session, default_tenant):
        """GREEN: lista permisos del tenant."""
        repo = PermisoRepository(db_session, default_tenant.id)
        await repo.create(codigo="p1", nombre="P1", modulo="m1")
        await repo.create(codigo="p2", nombre="P2", modulo="m2")

        permisos = await repo.list()
        assert len(permisos) == 2


class TestRolPermisoRepository:
    """Tests para RolPermisoRepository."""

    @pytest.fixture
    async def seed_rbac(self, db_session, default_tenant):
        """Crea rol y permiso para tests de RolPermiso."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)

        rol = await rol_repo.create(codigo="R1", nombre="R1")
        perm = await perm_repo.create(codigo="p:1", nombre="P1", modulo="m1")
        return rol, perm

    @pytest.mark.asyncio
    async def test_list_by_rol(self, db_session, default_tenant, seed_rbac):
        """RED: listar asignaciones por rol."""
        rol, perm = seed_rbac
        repo = RolPermisoRepository(db_session, default_tenant.id)
        rp = await repo.create(rol_id=rol.id, permiso_id=perm.id, es_propio=True)

        result = await repo.list_by_rol(rol.id)
        assert len(result) == 1
        assert result[0].id == rp.id

    @pytest.mark.asyncio
    async def test_list_by_permiso(self, db_session, default_tenant, seed_rbac):
        """GREEN: listar asignaciones por permiso."""
        rol, perm = seed_rbac
        repo = RolPermisoRepository(db_session, default_tenant.id)
        rp = await repo.create(rol_id=rol.id, permiso_id=perm.id)

        result = await repo.list_by_permiso(perm.id)
        assert len(result) == 1
        assert result[0].id == rp.id

    @pytest.mark.asyncio
    async def test_get_permissions_for_roles(self, db_session, default_tenant, seed_rbac):
        """TRIANGULATE: resolución de permisos efectivos."""
        rol, perm = seed_rbac
        repo = RolPermisoRepository(db_session, default_tenant.id)
        await repo.create(rol_id=rol.id, permiso_id=perm.id, es_propio=True)

        perms = await repo.get_permissions_for_roles([rol.codigo])
        assert ("p:1", True) in perms

    @pytest.mark.asyncio
    async def test_get_permissions_for_roles_union(self, db_session, default_tenant):
        """TRIANGULATE: unión de permisos de múltiples roles."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        rol_a = await rol_repo.create(codigo="ROL_A", nombre="Rol A")
        rol_b = await rol_repo.create(codigo="ROL_B", nombre="Rol B")
        perm_x = await perm_repo.create(codigo="px", nombre="PX", modulo="m")
        perm_y = await perm_repo.create(codigo="py", nombre="PY", modulo="m")

        await rp_repo.create(rol_id=rol_a.id, permiso_id=perm_x.id, es_propio=False)
        await rp_repo.create(rol_id=rol_b.id, permiso_id=perm_y.id, es_propio=True)

        perms = await rp_repo.get_permissions_for_roles(["ROL_A", "ROL_B"])
        assert ("px", False) in perms
        assert ("py", True) in perms

    @pytest.mark.asyncio
    async def test_get_permissions_for_roles_other_tenant_isolated(self, db_session, default_tenant):
        """TRIANGULATE: permisos de otro tenant no aparecen."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        rol = await rol_repo.create(codigo="ISOL", nombre="Isol")
        perm = await perm_repo.create(codigo="p:is", nombre="P Is", modulo="m")
        await rp_repo.create(rol_id=rol.id, permiso_id=perm.id)

        # Otro tenant con mismo código de rol no debe traer permisos
        other_repo = RolPermisoRepository(db_session, uuid4())
        perms = await other_repo.get_permissions_for_roles(["ISOL"])
        assert len(perms) == 0

    @pytest.mark.asyncio
    async def test_soft_delete_rol_permiso(self, db_session, default_tenant, seed_rbac):
        """TRIANGULATE: soft delete en RolPermiso."""
        rol, perm = seed_rbac
        repo = RolPermisoRepository(db_session, default_tenant.id)
        rp = await repo.create(rol_id=rol.id, permiso_id=perm.id)

        deleted = await repo.delete(rp.id)
        assert deleted is True
        assert rp.deleted_at is not None

        result = await repo.list_by_rol(rol.id)
        assert len(result) == 0
