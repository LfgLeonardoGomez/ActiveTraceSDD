"""Schemas Pydantic para asignaciones de rol en contexto académico (C-07).

Todos los schemas tienen extra='forbid' (regla dura).
AsignacionRead incluye estado_vigencia como campo computado desde el @property del modelo.
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AsignacionCreate(BaseModel):
    """Schema para crear una asignación."""

    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    rol: str = Field(..., min_length=1)
    desde: date
    hasta: date | None = None
    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    comisiones: list[str] | None = Field(default_factory=list)
    responsable_id: UUID | None = None


class AsignacionUpdate(BaseModel):
    """Schema para actualización parcial de asignación. Todos los campos opcionales."""

    model_config = ConfigDict(extra="forbid")

    rol: str | None = Field(None, min_length=1)
    desde: date | None = None
    hasta: date | None = None
    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    comisiones: list[str] | None = None
    responsable_id: UUID | None = None


class AsignacionRead(BaseModel):
    """Schema de respuesta de asignación — incluye estado_vigencia computado."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID
    tenant_id: UUID
    usuario_id: UUID
    rol: str
    desde: date
    hasta: date | None = None
    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    comisiones: list[str] | None = None
    responsable_id: UUID | None = None
    # Computado desde @property estado_vigencia del modelo ORM
    estado_vigencia: str


class PaginatedAsignacionesResponse(BaseModel):
    """Response paginado de asignaciones."""

    model_config = ConfigDict(extra="forbid")

    items: list[AsignacionRead]
    total: int
    limit: int
    offset: int
