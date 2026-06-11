"""Tests TDD para schemas de tareas (C-16).

Strict TDD: RED → GREEN → TRIANGULATE.
Sin base de datos: validación de schemas Pydantic v2.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4, UUID


# ---------------------------------------------------------------------------
# Grupo 1: Schemas de Tarea (CRUD)
# ---------------------------------------------------------------------------


class TestTareaSchemas:
    """Task 3.1: validación de schemas Tarea."""

    def test_tarea_create_requiere_campos_obligatorios(self) -> None:
        """RED: TareaCreate requiere titulo y asignado_a."""
        from pydantic import ValidationError
        from app.schemas.tarea import TareaCreateSchema

        with pytest.raises(ValidationError):
            TareaCreateSchema(titulo="Solo título")

    def test_tarea_create_valido(self) -> None:
        """GREEN: TareaCreate acepta campos correctos."""
        from app.schemas.tarea import TareaCreateSchema

        assignee_id = uuid4()
        obj = TareaCreateSchema(
            titulo="Tarea de prueba",
            descripcion="Descripción",
            criterio_cierre="Criterio",
            asignado_a=assignee_id,
        )
        assert obj.titulo == "Tarea de prueba"
        assert obj.descripcion == "Descripción"
        assert obj.criterio_cierre == "Criterio"
        assert obj.asignado_a == assignee_id
        assert obj.materia_id is None
        assert obj.contexto_id is None

    def test_tarea_create_rechaza_campos_extra(self) -> None:
        """GREEN: TareaCreate rechaza campos no declarados (extra='forbid')."""
        from pydantic import ValidationError
        from app.schemas.tarea import TareaCreateSchema

        with pytest.raises(ValidationError):
            TareaCreateSchema(
                titulo="Tarea",
                asignado_a=uuid4(),
                campo_extra="x",
            )

    def test_tarea_create_con_opcionales(self) -> None:
        """TRIANGULATE: TareaCreate acepta materia_id, contexto_id."""
        from app.schemas.tarea import TareaCreateSchema

        materia_id = uuid4()
        contexto_id = uuid4()
        obj = TareaCreateSchema(
            titulo="Tarea",
            asignado_a=uuid4(),
            materia_id=materia_id,
            contexto_id=contexto_id,
        )
        assert obj.materia_id == materia_id
        assert obj.contexto_id == contexto_id

    def test_tarea_update_todos_opcionales(self) -> None:
        """GREEN: TareaUpdate todos los campos son opcionales."""
        from app.schemas.tarea import TareaUpdateSchema

        obj = TareaUpdateSchema()
        assert obj.titulo is None
        assert obj.descripcion is None
        assert obj.criterio_cierre is None

    def test_tarea_update_rechaza_campos_extra(self) -> None:
        """GREEN: TareaUpdate rechaza campos extra (extra='forbid')."""
        from pydantic import ValidationError
        from app.schemas.tarea import TareaUpdateSchema

        with pytest.raises(ValidationError):
            TareaUpdateSchema(titulo="Tarea", campo_extra="x")

    def test_tarea_response_schema_todos_campos(self) -> None:
        """GREEN: TareaResponseSchema incluye todos los campos + timestamps."""
        from app.schemas.tarea import TareaResponseSchema, EstadoTarea

        now = datetime.now(timezone.utc)
        obj = TareaResponseSchema(
            id=uuid4(),
            tenant_id=uuid4(),
            titulo="Tarea",
            descripcion="Desc",
            criterio_cierre="Criterio",
            estado=EstadoTarea.PENDIENTE,
            aprobada=False,
            devuelta=False,
            asignado_a=uuid4(),
            asignado_por=uuid4(),
            revisada_por=None,
            revisada_at=None,
            materia_id=None,
            contexto_id=None,
            created_at=now,
            updated_at=now,
        )
        assert obj.id is not None
        assert obj.estado == EstadoTarea.PENDIENTE
        assert obj.aprobada is False

    def test_tarea_list_response_schema(self) -> None:
        """GREEN: TareaListResponseSchema paginado."""
        from app.schemas.tarea import TareaListResponseSchema

        obj = TareaListResponseSchema(
            items=[],
            total=0,
            page=1,
            pages=0,
        )
        assert obj.total == 0
        assert obj.page == 1


# ---------------------------------------------------------------------------
# Grupo 2: Schemas de estado y acciones
# ---------------------------------------------------------------------------


class TestTareaEstadoSchemas:
    """Task 3.1: schemas de estado y acciones."""

    def test_tarea_estado_schema(self) -> None:
        """RED: TareaEstadoSchema acepta EstadoTarea válido."""
        from app.schemas.tarea import TareaEstadoSchema, EstadoTarea

        obj = TareaEstadoSchema(estado=EstadoTarea.EN_PROGRESO)
        assert obj.estado == EstadoTarea.EN_PROGRESO

    def test_tarea_estado_schema_rechaza_extra(self) -> None:
        """GREEN: TareaEstadoSchema rechaza campos extra."""
        from pydantic import ValidationError
        from app.schemas.tarea import TareaEstadoSchema, EstadoTarea

        with pytest.raises(ValidationError):
            TareaEstadoSchema(estado=EstadoTarea.RESUELTA, extra="x")

    def test_devolver_tarea_schema(self) -> None:
        """GREEN: DevolverTareaSchema requiere observacion."""
        from app.schemas.tarea import DevolverTareaSchema

        obj = DevolverTareaSchema(observacion="Necesita rework")
        assert obj.observacion == "Necesita rework"

    def test_delegar_tarea_schema(self) -> None:
        """GREEN: DelegarTareaSchema requiere UUID."""
        from app.schemas.tarea import DelegarTareaSchema

        nuevo_id = uuid4()
        obj = DelegarTareaSchema(nuevo_asignado_id=nuevo_id)
        assert obj.nuevo_asignado_id == nuevo_id


# ---------------------------------------------------------------------------
# Grupo 3: Schemas de Comentario
# ---------------------------------------------------------------------------


class TestComentarioSchemas:
    """Task 3.1: schemas de comentarios."""

    def test_comentario_create_schema(self) -> None:
        """RED: ComentarioCreateSchema requiere contenido."""
        from app.schemas.tarea import ComentarioCreateSchema

        obj = ComentarioCreateSchema(contenido="Un comentario")
        assert obj.contenido == "Un comentario"

    def test_comentario_create_rechaza_extra(self) -> None:
        """GREEN: ComentarioCreateSchema rechaza campos extra."""
        from pydantic import ValidationError
        from app.schemas.tarea import ComentarioCreateSchema

        with pytest.raises(ValidationError):
            ComentarioCreateSchema(contenido="OK", extra="x")

    def test_comentario_response_schema(self) -> None:
        """GREEN: ComentarioResponseSchema estructura correcta."""
        from app.schemas.tarea import ComentarioResponseSchema

        now = datetime.now(timezone.utc)
        obj = ComentarioResponseSchema(
            id=uuid4(),
            tarea_id=uuid4(),
            autor_id=uuid4(),
            contenido="Contenido",
            created_at=now,
            updated_at=now,
        )
        assert obj.tarea_id is not None
        assert obj.autor_id is not None

    def test_comentario_list_response_schema(self) -> None:
        """GREEN: ComentarioListResponseSchema paginado."""
        from app.schemas.tarea import ComentarioListResponseSchema

        obj = ComentarioListResponseSchema(
            items=[],
            total=0,
            page=1,
            pages=0,
        )
        assert obj.total == 0


# ---------------------------------------------------------------------------
# Grupo 4: Enums
# ---------------------------------------------------------------------------


class TestEstadoTareaEnum:
    """Validación de enums StrEnum."""

    def test_estado_tarea_valores(self) -> None:
        """GREEN: EstadoTarea tiene 4 valores."""
        from app.schemas.tarea import EstadoTarea

        assert EstadoTarea.PENDIENTE == "Pendiente"
        assert EstadoTarea.EN_PROGRESO == "En progreso"
        assert EstadoTarea.RESUELTA == "Resuelta"
        assert EstadoTarea.CANCELADA == "Cancelada"

    def test_estado_tarea_desde_string_valido(self) -> None:
        """GREEN: EstadoTarea se puede instanciar desde string."""
        from app.schemas.tarea import EstadoTarea

        assert EstadoTarea("Pendiente") == EstadoTarea.PENDIENTE
        assert EstadoTarea("En progreso") == EstadoTarea.EN_PROGRESO

    def test_estado_tarea_desde_string_invalido(self) -> None:
        """RED: EstadoTarea rechaza string inválido."""
        from app.schemas.tarea import EstadoTarea

        with pytest.raises(ValueError):
            EstadoTarea("Invalido")
