"""Tests unitarios para schemas de avisos (C-15).

Sin base de datos: validación de schemas Pydantic v2.
Strict TDD: RED → GREEN → TRIANGULATE para extra='forbid'.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID


# ============================================================
# GRUPO 1: Schemas de Aviso (CRUD)
# ============================================================


class TestAvisoSchemas:
    """Task 7.1: validación de schemas Aviso."""

    def test_aviso_create_requiere_campos_obligatorios(self) -> None:
        """RED: AvisoCreate requiere alcance, severidad, titulo, cuerpo, inicio_en, fin_en."""
        from pydantic import ValidationError
        from app.schemas.aviso import AvisoCreate

        with pytest.raises(ValidationError):
            AvisoCreate(titulo="Solo título")

    def test_aviso_create_valido(self) -> None:
        """GREEN: AvisoCreate acepta campos correctos."""
        from app.schemas.aviso import AvisoCreate, AlcanceAviso, SeveridadAviso

        now = datetime.now(timezone.utc)
        obj = AvisoCreate(
            alcance=AlcanceAviso.GLOBAL,
            severidad=SeveridadAviso.INFO,
            titulo="Aviso de prueba",
            cuerpo="Contenido del aviso",
            inicio_en=now,
            fin_en=now + timedelta(days=7),
        )
        assert obj.alcance == AlcanceAviso.GLOBAL
        assert obj.severidad == SeveridadAviso.INFO
        assert obj.titulo == "Aviso de prueba"
        assert obj.activo is True
        assert obj.requiere_ack is False
        assert obj.orden == 0

    def test_aviso_create_rechaza_campos_extra(self) -> None:
        """GREEN: AvisoCreate rechaza campos no declarados (extra='forbid')."""
        from pydantic import ValidationError
        from app.schemas.aviso import AvisoCreate, AlcanceAviso, SeveridadAviso

        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            AvisoCreate(
                alcance=AlcanceAviso.GLOBAL,
                severidad=SeveridadAviso.INFO,
                titulo="Aviso",
                cuerpo="Contenido",
                inicio_en=now,
                fin_en=now + timedelta(days=1),
                campo_extra="x",
            )

    def test_aviso_create_con_opcionales(self) -> None:
        """GREEN: AvisoCreate acepta materia_id, cohorte_id, rol_destino, requiere_ack."""
        from app.schemas.aviso import AvisoCreate, AlcanceAviso, SeveridadAviso

        now = datetime.now(timezone.utc)
        materia_id = uuid4()
        cohorte_id = uuid4()
        obj = AvisoCreate(
            alcance=AlcanceAviso.POR_MATERIA,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            rol_destino="PROFESOR",
            severidad=SeveridadAviso.CRITICO,
            titulo="Aviso importante",
            cuerpo="Contenido",
            inicio_en=now,
            fin_en=now + timedelta(days=1),
            orden=5,
            activo=True,
            requiere_ack=True,
        )
        assert obj.materia_id == materia_id
        assert obj.cohorte_id == cohorte_id
        assert obj.rol_destino == "PROFESOR"
        assert obj.orden == 5
        assert obj.requiere_ack is True

    def test_aviso_update_todos_opcionales(self) -> None:
        """GREEN: AvisoUpdate todos los campos son opcionales."""
        from app.schemas.aviso import AvisoUpdate

        obj = AvisoUpdate()
        assert obj.titulo is None
        assert obj.cuerpo is None
        assert obj.alcance is None

    def test_aviso_update_rechaza_campos_extra(self) -> None:
        """GREEN: AvisoUpdate rechaza campos extra (extra='forbid')."""
        from pydantic import ValidationError
        from app.schemas.aviso import AvisoUpdate

        with pytest.raises(ValidationError):
            AvisoUpdate(titulo="Aviso", campo_extra="x")

    def test_aviso_response_schema_todos_campos(self) -> None:
        """GREEN: AvisoResponseSchema incluye todos los campos + timestamps."""
        from app.schemas.aviso import AvisoResponseSchema, AlcanceAviso, SeveridadAviso

        now = datetime.now(timezone.utc)
        obj = AvisoResponseSchema(
            id=uuid4(),
            tenant_id=uuid4(),
            alcance=AlcanceAviso.GLOBAL,
            materia_id=None,
            cohorte_id=None,
            rol_destino=None,
            severidad=SeveridadAviso.INFO,
            titulo="Test",
            cuerpo="Contenido",
            inicio_en=now,
            fin_en=now + timedelta(days=1),
            orden=0,
            activo=True,
            requiere_ack=False,
            created_at=now,
            updated_at=now,
        )
        assert obj.id is not None
        assert obj.tenant_id is not None
        assert obj.created_at is not None
        assert obj.updated_at is not None

    def test_aviso_list_response_schema(self) -> None:
        """GREEN: AvisoListResponseSchema paginado."""
        from app.schemas.aviso import AvisoListResponseSchema

        obj = AvisoListResponseSchema(
            items=[],
            total=0,
            page=1,
            pages=0,
        )
        assert obj.total == 0
        assert obj.page == 1


# ============================================================
# GRUPO 2: Schemas de Aviso para Usuario (mis-avisos)
# ============================================================


class TestAvisoParaUsuarioSchemas:
    """Task 7.1: schemas para visualización de usuario."""

    def test_aviso_para_usuario_con_acknowledged(self) -> None:
        """GREEN: AvisoParaUsuarioSchema incluye flag acknowledged."""
        from app.schemas.aviso import AvisoParaUsuarioSchema, AlcanceAviso, SeveridadAviso

        now = datetime.now(timezone.utc)
        obj = AvisoParaUsuarioSchema(
            id=uuid4(),
            tenant_id=uuid4(),
            alcance=AlcanceAviso.GLOBAL,
            materia_id=None,
            cohorte_id=None,
            rol_destino=None,
            severidad=SeveridadAviso.INFO,
            titulo="Test",
            cuerpo="Contenido",
            inicio_en=now,
            fin_en=now + timedelta(days=1),
            orden=0,
            activo=True,
            requiere_ack=False,
            created_at=now,
            updated_at=now,
            acknowledged=False,
        )
        assert obj.acknowledged is False

    def test_aviso_para_usuario_rechaza_extra(self) -> None:
        """GREEN: AvisoParaUsuarioSchema rechaza campos extra (extra='forbid')."""
        from pydantic import ValidationError
        from app.schemas.aviso import AvisoParaUsuarioSchema, AlcanceAviso, SeveridadAviso

        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            AvisoParaUsuarioSchema(
                id=uuid4(),
                tenant_id=uuid4(),
                alcance=AlcanceAviso.GLOBAL,
                materia_id=None,
                cohorte_id=None,
                rol_destino=None,
                severidad=SeveridadAviso.INFO,
                titulo="Test",
                cuerpo="Contenido",
                inicio_en=now,
                fin_en=now + timedelta(days=1),
                orden=0,
                activo=True,
                requiere_ack=False,
                created_at=now,
                updated_at=now,
                acknowledged=False,
                campo_extra="x",
            )

    def test_aviso_para_usuario_list_schema(self) -> None:
        """GREEN: AvisoParaUsuarioListSchema paginado."""
        from app.schemas.aviso import AvisoParaUsuarioListSchema

        obj = AvisoParaUsuarioListSchema(
            items=[],
            total=0,
            page=1,
            pages=0,
        )
        assert obj.total == 0


# ============================================================
# GRUPO 3: Schemas de Acknowledgment
# ============================================================


class TestAcknowledgmentSchemas:
    """Task 7.1: schemas de confirmación de lectura."""

    def test_acknowledgment_response_schema(self) -> None:
        """GREEN: AcknowledgmentResponseSchema estructura correcta."""
        from app.schemas.aviso import AcknowledgmentResponseSchema

        now = datetime.now(timezone.utc)
        obj = AcknowledgmentResponseSchema(
            id=uuid4(),
            aviso_id=uuid4(),
            usuario_id=uuid4(),
            confirmado_at=now,
            created_at=now,
        )
        assert obj.aviso_id is not None
        assert obj.usuario_id is not None
        assert obj.confirmado_at is not None

    def test_acknowledgment_rechaza_extra(self) -> None:
        """GREEN: AcknowledgmentResponseSchema rechaza campos extra (extra='forbid')."""
        from pydantic import ValidationError
        from app.schemas.aviso import AcknowledgmentResponseSchema

        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            AcknowledgmentResponseSchema(
                id=uuid4(),
                aviso_id=uuid4(),
                usuario_id=uuid4(),
                confirmado_at=now,
                created_at=now,
                campo_extra="x",
            )


# ============================================================
# GRUPO 4: Enums
# ============================================================


class TestAvisoEnums:
    """Validación de enums StrEnum."""

    def test_alcance_aviso_valores(self) -> None:
        """GREEN: AlcanceAviso tiene 4 valores."""
        from app.schemas.aviso import AlcanceAviso

        assert AlcanceAviso.GLOBAL == "Global"
        assert AlcanceAviso.POR_MATERIA == "PorMateria"
        assert AlcanceAviso.POR_COHORTE == "PorCohorte"
        assert AlcanceAviso.POR_ROL == "PorRol"

    def test_severidad_aviso_valores(self) -> None:
        """GREEN: SeveridadAviso tiene 3 valores."""
        from app.schemas.aviso import SeveridadAviso

        assert SeveridadAviso.INFO == "Info"
        assert SeveridadAviso.ADVERTENCIA == "Advertencia"
        assert SeveridadAviso.CRITICO == "Crítico"

    def test_alcance_desde_string_valido(self) -> None:
        """GREEN: AlcanceAviso se puede instanciar desde string."""
        from app.schemas.aviso import AlcanceAviso

        assert AlcanceAviso("Global") == AlcanceAviso.GLOBAL
        assert AlcanceAviso("PorMateria") == AlcanceAviso.POR_MATERIA

    def test_alcance_desde_string_invalido(self) -> None:
        """RED: AlcanceAviso rechaza string inválido."""
        from app.schemas.aviso import AlcanceAviso

        with pytest.raises(ValueError):
            AlcanceAviso("Invalido")

    def test_severidad_desde_string_valido(self) -> None:
        """GREEN: SeveridadAviso se puede instanciar desde string."""
        from app.schemas.aviso import SeveridadAviso

        assert SeveridadAviso("Crítico") == SeveridadAviso.CRITICO

    def test_severidad_desde_string_invalido(self) -> None:
        """RED: SeveridadAviso rechaza string inválido."""
        from app.schemas.aviso import SeveridadAviso

        with pytest.raises(ValueError):
            SeveridadAviso("Invalido")
