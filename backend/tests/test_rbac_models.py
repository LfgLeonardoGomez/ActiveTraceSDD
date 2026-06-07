"""Tests de TDD para modelos RBAC: Rol, Permiso, RolPermiso.

Verifica que los modelos ORM tengan las columnas correctas y
que las relaciones funcionen.
"""

import pytest
from sqlalchemy import select

from app.models.role import Rol, Permiso, RolPermiso


class TestRolModel:
    """Tests para modelo Rol."""

    @pytest.mark.asyncio
    async def test_rol_has_codigo_column(self, db_session, default_tenant):
        """RED: Rol debe tener columna codigo."""
        rol = Rol(
            tenant_id=default_tenant.id,
            codigo="TEST_ROL",
            nombre="Rol de Test",
            descripcion="Descripción de test",
        )
        db_session.add(rol)
        await db_session.commit()
        await db_session.refresh(rol)

        assert rol.codigo == "TEST_ROL"

    @pytest.mark.asyncio
    async def test_rol_codigo_unique_per_tenant(self, db_session, default_tenant):
        """GREEN: codigo debe ser único por tenant."""
        rol1 = Rol(
            tenant_id=default_tenant.id,
            codigo="UNIQ",
            nombre="Rol 1",
        )
        db_session.add(rol1)
        await db_session.commit()

        from sqlalchemy.exc import IntegrityError
        rol2 = Rol(
            tenant_id=default_tenant.id,
            codigo="UNIQ",
            nombre="Rol 2",
        )
        db_session.add(rol2)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_rol_soft_delete(self, db_session, default_tenant):
        """TRIANGULATE: soft delete funciona en Rol."""
        from datetime import datetime, timezone
        rol = Rol(
            tenant_id=default_tenant.id,
            codigo="SOFT_DEL",
            nombre="Rol a eliminar",
        )
        db_session.add(rol)
        await db_session.commit()

        rol.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()

        result = await db_session.execute(
            select(Rol).where(Rol.codigo == "SOFT_DEL", Rol.deleted_at.is_(None))
        )
        assert result.scalar_one_or_none() is None


class TestPermisoModel:
    """Tests para modelo Permiso."""

    @pytest.mark.asyncio
    async def test_permiso_has_codigo_column(self, db_session, default_tenant):
        """RED: Permiso debe tener columna codigo."""
        permiso = Permiso(
            tenant_id=default_tenant.id,
            codigo="test:ver",
            nombre="Ver test",
            modulo="test",
            descripcion="Permiso de test",
        )
        db_session.add(permiso)
        await db_session.commit()
        await db_session.refresh(permiso)

        assert permiso.codigo == "test:ver"

    @pytest.mark.asyncio
    async def test_permiso_codigo_unique_per_tenant(self, db_session, default_tenant):
        """GREEN: codigo debe ser único por tenant."""
        p1 = Permiso(
            tenant_id=default_tenant.id,
            codigo="UNIQ_P",
            nombre="P1",
            modulo="test",
        )
        db_session.add(p1)
        await db_session.commit()

        from sqlalchemy.exc import IntegrityError
        p2 = Permiso(
            tenant_id=default_tenant.id,
            codigo="UNIQ_P",
            nombre="P2",
            modulo="test",
        )
        db_session.add(p2)
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestRolPermisoModel:
    """Tests para modelo RolPermiso."""

    @pytest.mark.asyncio
    async def test_rol_permiso_exists(self, db_session, default_tenant):
        """RED: RolPermiso debe existir como modelo."""
        rol = Rol(
            tenant_id=default_tenant.id,
            codigo="ROL_RP",
            nombre="Rol RP",
        )
        permiso = Permiso(
            tenant_id=default_tenant.id,
            codigo="permiso:rp",
            nombre="Permiso RP",
            modulo="rp",
        )
        db_session.add_all([rol, permiso])
        await db_session.commit()

        rp = RolPermiso(
            tenant_id=default_tenant.id,
            rol_id=rol.id,
            permiso_id=permiso.id,
            es_propio=True,
        )
        db_session.add(rp)
        await db_session.commit()
        await db_session.refresh(rp)

        assert rp.es_propio is True
        assert rp.rol_id == rol.id
        assert rp.permiso_id == permiso.id

    @pytest.mark.asyncio
    async def test_rol_permiso_es_propio_default_false(self, db_session, default_tenant):
        """GREEN: es_propio default false."""
        rol = Rol(
            tenant_id=default_tenant.id,
            codigo="ROL_RP2",
            nombre="Rol RP2",
        )
        permiso = Permiso(
            tenant_id=default_tenant.id,
            codigo="permiso:rp2",
            nombre="Permiso RP2",
            modulo="rp2",
        )
        db_session.add_all([rol, permiso])
        await db_session.commit()

        rp = RolPermiso(
            tenant_id=default_tenant.id,
            rol_id=rol.id,
            permiso_id=permiso.id,
        )
        db_session.add(rp)
        await db_session.commit()
        await db_session.refresh(rp)

        assert rp.es_propio is False

    @pytest.mark.asyncio
    async def test_rol_permiso_soft_delete(self, db_session, default_tenant):
        """TRIANGULATE: soft delete en RolPermiso."""
        from datetime import datetime, timezone
        rol = Rol(
            tenant_id=default_tenant.id,
            codigo="ROL_RP3",
            nombre="Rol RP3",
        )
        permiso = Permiso(
            tenant_id=default_tenant.id,
            codigo="permiso:rp3",
            nombre="Permiso RP3",
            modulo="rp3",
        )
        db_session.add_all([rol, permiso])
        await db_session.commit()

        rp = RolPermiso(
            tenant_id=default_tenant.id,
            rol_id=rol.id,
            permiso_id=permiso.id,
        )
        db_session.add(rp)
        await db_session.commit()

        rp.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()

        result = await db_session.execute(
            select(RolPermiso).where(RolPermiso.id == rp.id, RolPermiso.deleted_at.is_(None))
        )
        assert result.scalar_one_or_none() is None
