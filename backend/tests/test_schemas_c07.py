"""Tests TDD para schemas Pydantic C-07: Usuario y Asignacion.

Strict TDD: RED → GREEN → TRIANGULATE para enmascaramiento de PII.
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4, UUID


# ============================================================
# GRUPO 9: Schemas de Usuario
# ============================================================


class TestUsuarioSchemasMascaraPII:
    """Task 9.3 RED → GREEN: enmascaramiento de PII en UsuarioListRead."""

    def test_usuario_create_requiere_campos_basicos(self) -> None:
        """RED 9.1: UsuarioCreate requiere nombre, apellidos, email, estado."""
        from pydantic import ValidationError
        from app.schemas.usuarios import UsuarioCreate

        with pytest.raises(ValidationError):
            UsuarioCreate(nombre="Solo nombre")

    def test_usuario_create_valido(self) -> None:
        """GREEN 9.1: UsuarioCreate acepta campos correctos."""
        from app.schemas.usuarios import UsuarioCreate

        obj = UsuarioCreate(
            nombre="Juan",
            apellidos="Pérez",
            email="juan@test.com",
            estado="Activo",
        )
        assert obj.email == "juan@test.com"

    def test_usuario_create_rechaza_campos_extra(self) -> None:
        """GREEN 9.1: UsuarioCreate rechaza campos no declarados (extra='forbid')."""
        from pydantic import ValidationError
        from app.schemas.usuarios import UsuarioCreate

        with pytest.raises(ValidationError):
            UsuarioCreate(
                nombre="Juan",
                apellidos="Pérez",
                email="juan@test.com",
                estado="Activo",
                campo_extra="x",
            )

    def test_usuario_update_todos_opcionales(self) -> None:
        """GREEN 9.1: UsuarioUpdate todos los campos son opcionales."""
        from app.schemas.usuarios import UsuarioUpdate

        obj = UsuarioUpdate()
        assert obj.nombre is None
        assert obj.email is None

    def test_usuario_list_read_enmascara_dni(self) -> None:
        """RED 9.3: UsuarioListRead enmascara dni con ****XXXX."""
        from app.schemas.usuarios import UsuarioListRead

        obj = UsuarioListRead(
            id=uuid4(),
            tenant_id=uuid4(),
            nombre="Test",
            apellidos="Usuario",
            email="test@test.com",
            estado="Activo",
            dni="12345678",
        )
        assert obj.dni == "****5678", f"Expected ****5678 but got {obj.dni}"

    def test_usuario_list_read_enmascara_cuil(self) -> None:
        """TRIANGULATE 9.3: UsuarioListRead enmascara cuil."""
        from app.schemas.usuarios import UsuarioListRead

        obj = UsuarioListRead(
            id=uuid4(),
            tenant_id=uuid4(),
            nombre="Test",
            apellidos="Usuario",
            email="cuil@test.com",
            estado="Activo",
            cuil="20-12345678-9",
        )
        # Últimos 4 del cuil
        assert "****" in obj.cuil
        assert obj.cuil.endswith(obj.cuil[-4:])

    def test_usuario_list_read_no_tiene_cbu(self) -> None:
        """RED 9.3: UsuarioListRead NO incluye campo cbu."""
        from app.schemas.usuarios import UsuarioListRead

        # El modelo no debe tener campo cbu
        fields = UsuarioListRead.model_fields
        assert "cbu" not in fields, "UsuarioListRead no debe incluir cbu"

    def test_usuario_list_read_no_tiene_alias_cbu(self) -> None:
        """TRIANGULATE 9.3: UsuarioListRead NO incluye alias_cbu."""
        from app.schemas.usuarios import UsuarioListRead

        fields = UsuarioListRead.model_fields
        assert "alias_cbu" not in fields, "UsuarioListRead no debe incluir alias_cbu"

    def test_usuario_detail_read_incluye_cbu(self) -> None:
        """GREEN 9.1: UsuarioDetailRead incluye cbu y alias_cbu."""
        from app.schemas.usuarios import UsuarioDetailRead

        fields = UsuarioDetailRead.model_fields
        assert "cbu" in fields
        assert "alias_cbu" in fields

    def test_usuario_detail_read_incluye_dni_sin_mascara(self) -> None:
        """GREEN 9.1: UsuarioDetailRead incluye dni sin máscara."""
        from app.schemas.usuarios import UsuarioDetailRead

        obj = UsuarioDetailRead(
            id=uuid4(),
            tenant_id=uuid4(),
            nombre="Test",
            apellidos="Usuario",
            email="detail@test.com",
            estado="Activo",
            dni="12345678",
            cuil="20-12345678-9",
            cbu="0720049240000001234567",
            alias_cbu="mi.alias",
        )
        assert obj.dni == "12345678"
        assert obj.cbu == "0720049240000001234567"

    def test_paginated_usuarios_response(self) -> None:
        """GREEN 9.1: PaginatedUsuariosResponse incluye items, total, limit, offset."""
        from app.schemas.usuarios import PaginatedUsuariosResponse, UsuarioListRead

        obj = PaginatedUsuariosResponse(
            items=[],
            total=0,
            limit=20,
            offset=0,
        )
        assert obj.total == 0
        assert obj.limit == 20


# ============================================================
# GRUPO 9: Schemas de Asignacion
# ============================================================


class TestAsignacionSchemas:
    """Task 9.2: schemas de Asignacion."""

    def test_asignacion_create_requiere_usuario_id_rol_desde(self) -> None:
        """RED 9.2: AsignacionCreate requiere usuario_id, rol, desde."""
        from pydantic import ValidationError
        from app.schemas.asignaciones import AsignacionCreate

        with pytest.raises(ValidationError):
            AsignacionCreate(rol="PROFESOR")  # Falta usuario_id y desde

    def test_asignacion_create_valido(self) -> None:
        """GREEN 9.2: AsignacionCreate acepta campos correctos."""
        from app.schemas.asignaciones import AsignacionCreate

        obj = AsignacionCreate(
            usuario_id=uuid4(),
            rol="PROFESOR",
            desde=date.today(),
        )
        assert obj.rol == "PROFESOR"
        assert obj.hasta is None

    def test_asignacion_create_rechaza_extra(self) -> None:
        """GREEN 9.2: AsignacionCreate rechaza campos extra."""
        from pydantic import ValidationError
        from app.schemas.asignaciones import AsignacionCreate

        with pytest.raises(ValidationError):
            AsignacionCreate(
                usuario_id=uuid4(),
                rol="TUTOR",
                desde=date.today(),
                campo_extra="x",
            )

    def test_asignacion_read_incluye_estado_vigencia(self) -> None:
        """GREEN 9.2: AsignacionRead incluye estado_vigencia como campo computado."""
        from app.schemas.asignaciones import AsignacionRead

        obj = AsignacionRead(
            id=uuid4(),
            tenant_id=uuid4(),
            usuario_id=uuid4(),
            rol="TUTOR",
            desde=date.today() - timedelta(days=10),
            hasta=date.today() + timedelta(days=30),
            estado_vigencia="Vigente",
        )
        assert obj.estado_vigencia == "Vigente"

    def test_asignacion_update_todos_opcionales(self) -> None:
        """GREEN 9.2: AsignacionUpdate todos los campos son opcionales."""
        from app.schemas.asignaciones import AsignacionUpdate

        obj = AsignacionUpdate()
        assert obj.rol is None
        assert obj.hasta is None

    def test_paginated_asignaciones_response(self) -> None:
        """GREEN 9.2: PaginatedAsignacionesResponse estructura correcta."""
        from app.schemas.asignaciones import PaginatedAsignacionesResponse

        obj = PaginatedAsignacionesResponse(
            items=[],
            total=0,
            limit=50,
            offset=0,
        )
        assert obj.total == 0
