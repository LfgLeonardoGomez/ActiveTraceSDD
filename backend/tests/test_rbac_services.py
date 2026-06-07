"""Tests de TDD para servicios RBAC.

Verifica lógica de negocio: resolución de permisos, CRUD y validaciones.
"""

import pytest
from uuid import uuid4

from app.models.role import Rol, Permiso, RolPermiso
from app.repositories.rbac_repository import (
    RolRepository,
    PermisoRepository,
    RolPermisoRepository,
)
from app.services.permission_service import PermissionService
from app.services.rbac_service import RolService, PermisoService, RolPermisoService


class TestPermissionService:
    """Tests para PermissionService."""

    @pytest.fixture
    async def seed_matrix(self, db_session, default_tenant):
        """Seed de matriz básica para tests de resolución."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        rol_a = await rol_repo.create(codigo="R_A", nombre="Rol A")
        rol_b = await rol_repo.create(codigo="R_B", nombre="Rol B")
        perm_x = await perm_repo.create(codigo="px", nombre="PX", modulo="m")
        perm_y = await perm_repo.create(codigo="py", nombre="PY", modulo="m")
        perm_z = await perm_repo.create(codigo="pz", nombre="PZ", modulo="m")

        await rp_repo.create(rol_id=rol_a.id, permiso_id=perm_x.id, es_propio=False)
        await rp_repo.create(rol_id=rol_a.id, permiso_id=perm_y.id, es_propio=True)
        await rp_repo.create(rol_id=rol_b.id, permiso_id=perm_y.id, es_propio=False)
        await rp_repo.create(rol_id=rol_b.id, permiso_id=perm_z.id, es_propio=True)

        return rol_a, rol_b

    @pytest.mark.asyncio
    async def test_resolve_single_role(self, db_session, default_tenant, seed_matrix):
        """RED: un solo rol devuelve sus permisos."""
        service = PermissionService(db_session, default_tenant.id)
        perms = await service.resolve_effective_permissions(["R_A"])

        assert ("px", False) in perms
        assert ("py", True) in perms
        assert ("pz", False) not in perms

    @pytest.mark.asyncio
    async def test_resolve_union_of_roles(self, db_session, default_tenant, seed_matrix):
        """GREEN: unión de múltiples roles."""
        service = PermissionService(db_session, default_tenant.id)
        perms = await service.resolve_effective_permissions(["R_A", "R_B"])

        assert ("px", False) in perms
        assert ("py", False) in perms  # Unión: es_propio=False prevalece cuando un rol lo tiene global
        assert ("pz", True) in perms

    @pytest.mark.asyncio
    async def test_resolve_empty_roles(self, db_session, default_tenant):
        """TRIANGULATE: lista vacía de roles → permisos vacíos."""
        service = PermissionService(db_session, default_tenant.id)
        perms = await service.resolve_effective_permissions([])
        assert perms == set()

    @pytest.mark.asyncio
    async def test_resolve_other_tenant_isolated(self, db_session, default_tenant, seed_matrix):
        """TRIANGULATE: permisos de otro tenant no se incluyen."""
        service = PermissionService(db_session, uuid4())
        perms = await service.resolve_effective_permissions(["R_A"])
        assert perms == set()


class TestRolService:
    """Tests para RolService."""

    @pytest.mark.asyncio
    async def test_create_rol(self, db_session, default_tenant):
        """RED: crear rol con validación de tenant."""
        service = RolService(db_session, default_tenant.id)
        rol = await service.create(codigo="SVC_R", nombre="Svc Rol")
        assert rol.codigo == "SVC_R"

    @pytest.mark.asyncio
    async def test_list_roles(self, db_session, default_tenant):
        """GREEN: listar roles del tenant."""
        service = RolService(db_session, default_tenant.id)
        await service.create(codigo="R1", nombre="R1")
        await service.create(codigo="R2", nombre="R2")

        roles = await service.list()
        assert len(roles) == 2

    @pytest.mark.asyncio
    async def test_soft_delete_rol(self, db_session, default_tenant):
        """TRIANGULATE: soft delete de rol."""
        service = RolService(db_session, default_tenant.id)
        rol = await service.create(codigo="DEL_SVC", nombre="Del Svc")
        deleted = await service.delete(rol.id)
        assert deleted is True

    @pytest.mark.asyncio
    async def test_get_by_id_and_codigo(self, db_session, default_tenant):
        """TRIANGULATE: obtener rol por id y por codigo."""
        service = RolService(db_session, default_tenant.id)
        rol = await service.create(codigo="GET_R", nombre="Get Rol")

        found_id = await service.get_by_id(rol.id)
        assert found_id is not None
        assert found_id.id == rol.id

        found_code = await service.get_by_codigo("GET_R")
        assert found_code is not None
        assert found_code.codigo == "GET_R"

    @pytest.mark.asyncio
    async def test_update_rol(self, db_session, default_tenant):
        """TRIANGULATE: actualizar rol."""
        service = RolService(db_session, default_tenant.id)
        rol = await service.create(codigo="UPD_R", nombre="Upd Rol")

        updated = await service.update(rol.id, {"nombre": "Updated"})
        assert updated is not None
        assert updated.nombre == "Updated"


class TestPermisoService:
    """Tests para PermisoService."""

    @pytest.mark.asyncio
    async def test_create_permiso(self, db_session, default_tenant):
        """RED: crear permiso."""
        service = PermisoService(db_session, default_tenant.id)
        perm = await service.create(codigo="svc:p", nombre="Svc P", modulo="svc")
        assert perm.codigo == "svc:p"

    @pytest.mark.asyncio
    async def test_list_permisos(self, db_session, default_tenant):
        """GREEN: listar permisos del tenant."""
        service = PermisoService(db_session, default_tenant.id)
        await service.create(codigo="p1", nombre="P1", modulo="m")
        await service.create(codigo="p2", nombre="P2", modulo="m")

        perms = await service.list()
        assert len(perms) == 2

    @pytest.mark.asyncio
    async def test_get_by_id_and_codigo(self, db_session, default_tenant):
        """TRIANGULATE: obtener permiso por id y codigo."""
        service = PermisoService(db_session, default_tenant.id)
        perm = await service.create(codigo="gp", nombre="GP", modulo="m")

        found_id = await service.get_by_id(perm.id)
        assert found_id is not None

        found_code = await service.get_by_codigo("gp")
        assert found_code is not None

    @pytest.mark.asyncio
    async def test_update_and_delete_permiso(self, db_session, default_tenant):
        """TRIANGULATE: actualizar y eliminar permiso."""
        service = PermisoService(db_session, default_tenant.id)
        perm = await service.create(codigo="ud", nombre="UD", modulo="m")

        updated = await service.update(perm.id, {"nombre": "Updated"})
        assert updated is not None

        deleted = await service.delete(perm.id)
        assert deleted is True


class TestRolPermisoService:
    """Tests para RolPermisoService."""

    @pytest.fixture
    async def seed_entities(self, db_session, default_tenant):
        """Crea rol y permiso para tests."""
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rol = await rol_repo.create(codigo="RPS_R", nombre="RPS Rol")
        perm = await perm_repo.create(codigo="rps:p", nombre="RPS Perm", modulo="rps")
        return rol, perm

    @pytest.mark.asyncio
    async def test_assign_permiso_to_rol(self, db_session, default_tenant, seed_entities):
        """RED: asignar permiso a rol."""
        rol, perm = seed_entities
        service = RolPermisoService(db_session, default_tenant.id)
        rp = await service.assign(rol_id=rol.id, permiso_id=perm.id, es_propio=True)

        assert rp.rol_id == rol.id
        assert rp.permiso_id == perm.id
        assert rp.es_propio is True

    @pytest.mark.asyncio
    async def test_assign_validates_same_tenant(self, db_session, default_tenant, seed_entities):
        """GREEN: valida que rol y permiso existan en el mismo tenant."""
        rol, perm = seed_entities
        service = RolPermisoService(db_session, uuid4())
        with pytest.raises(ValueError, match="rol o permiso no existe"):
            await service.assign(rol_id=rol.id, permiso_id=perm.id)

    @pytest.mark.asyncio
    async def test_remove_assignment(self, db_session, default_tenant, seed_entities):
        """TRIANGULATE: quitar asignación (soft delete)."""
        rol, perm = seed_entities
        service = RolPermisoService(db_session, default_tenant.id)
        rp = await service.assign(rol_id=rol.id, permiso_id=perm.id)

        removed = await service.remove(rp.id)
        assert removed is True
        assert rp.deleted_at is not None

    @pytest.mark.asyncio
    async def test_list_by_rol_and_permiso(self, db_session, default_tenant, seed_entities):
        """TRIANGULATE: listar por rol y por permiso."""
        rol, perm = seed_entities
        service = RolPermisoService(db_session, default_tenant.id)
        rp = await service.assign(rol_id=rol.id, permiso_id=perm.id)

        by_rol = await service.list_by_rol(rol.id)
        assert len(by_rol) == 1

        by_perm = await service.list_by_permiso(perm.id)
        assert len(by_perm) == 1
