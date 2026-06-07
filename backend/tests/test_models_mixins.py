"""Tests de TDD para modelos y mixins — C-02 Task Group 1."""

import pytest
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base
from app.models.tenant import Tenant
from app.models.mixins import BaseModelMixin
from app.models.user import Usuario
from app.models.role import Rol, Permiso


class TestTenantModel:
    """RED/GREEN/TRIANGULATE/REFACTOR para Tenant."""

    @pytest.mark.asyncio
    async def test_tenant_creation(self, db_session):
        """RED: crear un tenant con campos mínimos persiste correctamente."""
        tenant = Tenant(
            nombre="Universidad Test",
            slug="universidad-test",
            activo=True,
            configuracion={"plan": "basic"},
        )
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        assert tenant.id is not None
        assert tenant.nombre == "Universidad Test"
        assert tenant.slug == "universidad-test"
        assert tenant.activo is True
        assert tenant.configuracion == {"plan": "basic"}
        assert tenant.created_at is not None
        assert tenant.updated_at is not None

    @pytest.mark.asyncio
    async def test_tenant_slug_uniqueness(self, db_session):
        """TRIANGULATE: slug duplicado viola constraint UNIQUE."""
        tenant1 = Tenant(nombre="T1", slug="same-slug", activo=True)
        tenant2 = Tenant(nombre="T2", slug="same-slug", activo=True)
        db_session.add(tenant1)
        await db_session.commit()
        db_session.add(tenant2)
        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_tenant_default_configuracion_none(self, db_session):
        """TRIANGULATE: configuracion puede ser None por default."""
        tenant = Tenant(nombre="Minimal", slug="minimal", activo=True)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)
        assert tenant.configuracion is None


class TestBaseModelMixin:
    """RED/GREEN/TRIANGULATE/REFACTOR para BaseModelMixin."""

    @pytest.mark.asyncio
    async def test_mixin_adds_core_fields(self, db_session, default_tenant):
        """RED: modelo con mixin tiene id, tenant_id, created_at, updated_at, deleted_at."""
        user = Usuario(
            tenant_id=default_tenant.id,
            nombre="Juan",
            apellidos="Perez",
            email="juan@example.com",
            estado="activo",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.tenant_id == default_tenant.id
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.deleted_at is None

    @pytest.mark.asyncio
    async def test_mixin_updated_at_changes_on_update(self, db_session, default_tenant):
        """GREEN: updated_at se actualiza automáticamente al modificar."""
        user = Usuario(
            tenant_id=default_tenant.id,
            nombre="Ana",
            apellidos="Garcia",
            email="ana@example.com",
            estado="activo",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        original_updated_at = user.updated_at

        # Esperar un momento para que el timestamp cambie
        import asyncio
        await asyncio.sleep(0.01)

        user.nombre = "Ana Maria"
        await db_session.commit()
        await db_session.refresh(user)

        assert user.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_all_domain_models_have_tenant_id(self, db_session, default_tenant):
        """TRIANGULATE: todos los modelos de dominio tienen tenant_id."""
        user = Usuario(
            tenant_id=default_tenant.id,
            nombre="User",
            apellidos="Test",
            email="user@test.com",
            estado="activo",
        )
        rol = Rol(tenant_id=default_tenant.id, nombre="Admin", descripcion="Admin role")
        permiso = Permiso(tenant_id=default_tenant.id, nombre="read", modulo="users")

        db_session.add_all([user, rol, permiso])
        await db_session.commit()

        assert user.tenant_id == default_tenant.id
        assert rol.tenant_id == default_tenant.id
        assert permiso.tenant_id == default_tenant.id

    @pytest.mark.asyncio
    async def test_base_metadata_has_all_tables(self, db_session):
        """TRIANGULATE: Base.metadata reconoce tenants, usuarios, roles, permisos."""
        table_names = list(Base.metadata.tables.keys())
        assert "tenants" in table_names
        assert "usuarios" in table_names
        assert "roles" in table_names
        assert "permisos" in table_names

    @pytest.mark.asyncio
    async def test_tenant_model_is_not_mixin(self, db_session):
        """TRIANGULATE: Tenant no tiene tenant_id ni deleted_at (es global)."""
        tenant = Tenant(nombre="Global", slug="global", activo=True)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)
        assert not hasattr(tenant, "tenant_id")
        assert not hasattr(tenant, "deleted_at")


class TestRoleAndPermissionModels:
    """RED/GREEN para modelos placeholder Rol y Permiso."""

    @pytest.mark.asyncio
    async def test_rol_creation(self, db_session, default_tenant):
        """RED: crear un Rol hereda BaseModelMixin y persiste."""
        rol = Rol(
            tenant_id=default_tenant.id,
            nombre="Profesor",
            descripcion="Rol docente",
        )
        db_session.add(rol)
        await db_session.commit()
        await db_session.refresh(rol)

        assert rol.id is not None
        assert rol.tenant_id == default_tenant.id
        assert rol.nombre == "Profesor"
        assert rol.created_at is not None

    @pytest.mark.asyncio
    async def test_permiso_creation(self, db_session, default_tenant):
        """RED: crear un Permiso hereda BaseModelMixin y persiste."""
        permiso = Permiso(
            tenant_id=default_tenant.id,
            nombre="ver_calificaciones",
            modulo="calificaciones",
            descripcion="Ver notas",
        )
        db_session.add(permiso)
        await db_session.commit()
        await db_session.refresh(permiso)

        assert permiso.id is not None
        assert permiso.tenant_id == default_tenant.id
        assert permiso.nombre == "ver_calificaciones"
        assert permiso.created_at is not None
