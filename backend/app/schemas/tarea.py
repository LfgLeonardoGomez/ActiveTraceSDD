"""Schemas Pydantic para tareas y comentarios (C-16).

Todos los schemas usan extra='forbid' (regla dura del proyecto).
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EstadoTarea(StrEnum):
    """Estados del ciclo de vida de una tarea interna."""

    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    RESUELTA = "Resuelta"
    CANCELADA = "Cancelada"


# ------------------------------------------------------------------
# Tarea CRUD
# ------------------------------------------------------------------


class TareaCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str = Field(..., min_length=1, max_length=300)
    descripcion: str | None = Field(default=None, min_length=1)
    criterio_cierre: str | None = Field(default=None, min_length=1)
    asignado_a: UUID
    materia_id: UUID | None = None
    contexto_id: UUID | None = None


class TareaUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, min_length=1, max_length=300)
    descripcion: str | None = Field(default=None, min_length=1)
    criterio_cierre: str | None = Field(default=None, min_length=1)
    asignado_a: UUID | None = None
    materia_id: UUID | None = None
    contexto_id: UUID | None = None


class TareaResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    titulo: str
    descripcion: str | None
    criterio_cierre: str | None
    estado: EstadoTarea
    aprobada: bool
    devuelta: bool
    asignado_a: UUID
    asignado_por: UUID
    revisada_por: UUID | None
    revisada_at: datetime | None
    materia_id: UUID | None
    contexto_id: UUID | None
    created_at: datetime
    updated_at: datetime


class TareaListResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[TareaResponseSchema]
    total: int
    page: int
    pages: int


# ------------------------------------------------------------------
# Estado y acciones
# ------------------------------------------------------------------


class TareaEstadoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: EstadoTarea


class DevolverTareaSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observacion: str = Field(..., min_length=1)


class DelegarTareaSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nuevo_asignado_id: UUID


# ------------------------------------------------------------------
# Comentarios
# ------------------------------------------------------------------


class ComentarioCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contenido: str = Field(..., min_length=1)


class ComentarioResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tarea_id: UUID
    autor_id: UUID
    contenido: str
    created_at: datetime
    updated_at: datetime


class ComentarioListResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ComentarioResponseSchema]
    total: int
    page: int
    pages: int
