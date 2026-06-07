"""Tests de TDD para schemas Pydantic de RBAC.

Verifica extra='forbid' y estructura de PermissionContext.
"""

import pytest
from pydantic import ValidationError

from app.schemas.rbac_schema import (
    RolCreateSchema,
    RolUpdateSchema,
    RolResponseSchema,
    PermisoCreateSchema,
    PermisoUpdateSchema,
    PermisoResponseSchema,
    RolPermisoCreateSchema,
    RolPermisoResponseSchema,
    PermissionContext,
)


class TestRolSchemas:
    """Tests para schemas de Rol."""

    def test_create_extra_forbidden(self):
        """RED: RolCreateSchema rechaza campos extra."""
        with pytest.raises(ValidationError):
            RolCreateSchema(codigo="R", nombre="R", extra_field="bad")

    def test_create_valid(self):
        """GREEN: RolCreateSchema acepta datos válidos."""
        schema = RolCreateSchema(codigo="R", nombre="Rol", descripcion="Desc")
        assert schema.codigo == "R"
        assert schema.descripcion == "Desc"

    def test_update_allows_partial(self):
        """TRIANGULATE: RolUpdateSchema permite campos parciales."""
        schema = RolUpdateSchema(nombre="Nuevo nombre")
        assert schema.nombre == "Nuevo nombre"
        assert schema.codigo is None

    def test_response_has_id(self):
        """TRIANGULATE: RolResponseSchema incluye id."""
        from uuid import uuid4
        uid = uuid4()
        schema = RolResponseSchema(id=uid, tenant_id=uuid4(), codigo="R", nombre="Rol")
        assert schema.id == uid


class TestPermisoSchemas:
    """Tests para schemas de Permiso."""

    def test_create_extra_forbidden(self):
        """RED: PermisoCreateSchema rechaza campos extra."""
        with pytest.raises(ValidationError):
            PermisoCreateSchema(codigo="p:a", nombre="P", modulo="m", extra="bad")

    def test_create_valid(self):
        """GREEN: PermisoCreateSchema acepta datos válidos."""
        schema = PermisoCreateSchema(codigo="p:a", nombre="P", modulo="m")
        assert schema.codigo == "p:a"


class TestRolPermisoSchemas:
    """Tests para schemas de RolPermiso."""

    def test_create_has_es_propio(self):
        """RED: RolPermisoCreateSchema incluye es_propio."""
        from uuid import uuid4
        schema = RolPermisoCreateSchema(
            rol_id=uuid4(), permiso_id=uuid4(), es_propio=True
        )
        assert schema.es_propio is True

    def test_create_es_propio_default_false(self):
        """GREEN: es_propio default false."""
        from uuid import uuid4
        schema = RolPermisoCreateSchema(rol_id=uuid4(), permiso_id=uuid4())
        assert schema.es_propio is False


class TestPermissionContext:
    """Tests para PermissionContext."""

    def test_has_permission_and_is_propio(self):
        """RED: PermissionContext tiene has_permission e is_propio."""
        ctx = PermissionContext(has_permission=True, is_propio=False)
        assert ctx.has_permission is True
        assert ctx.is_propio is False

    def test_effective_permissions_set(self):
        """GREEN: effective_permissions es un set de strings."""
        ctx = PermissionContext(
            has_permission=True,
            is_propio=False,
            effective_permissions={"comunicacion:enviar", "avisos:confirmar"},
        )
        assert "comunicacion:enviar" in ctx.effective_permissions

    def test_extra_forbidden(self):
        """TRIANGULATE: PermissionContext rechaza campos extra."""
        with pytest.raises(ValidationError):
            PermissionContext(has_permission=True, is_propio=False, bad_field="x")
