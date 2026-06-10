"""Schemas Pydantic para guardias (C-13).

Todos los schemas tienen extra='forbid' (regla dura del proyecto).
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------------------------------------
# Guardia schemas
# ------------------------------------------------------------------

class GuardiaCreate(BaseModel):
    """Schema para crear una guardia."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    fecha: date
    horario: str | None = Field(
        None,
        pattern=r"^\d{2}:\d{2}[-\u2013]\d{2}:\d{2}$",
    )
    descripcion: str = Field(..., min_length=1)


class GuardiaUpdate(BaseModel):
    """Schema para actualización parcial de guardia."""

    model_config = ConfigDict(extra="forbid")

    fecha: date | None = None
    horario: str | None = Field(
        None,
        pattern=r"^\d{2}:\d{2}[-\u2013]\d{2}:\d{2}$",
    )
    descripcion: str | None = Field(None, min_length=1)
    estado: str | None = Field(None, pattern=r"^(Pendiente|Realizada|Cancelada)$")
    comentarios: str | None = None


class GuardiaRead(BaseModel):
    """Schema de respuesta de guardia."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID
    tenant_id: UUID
    tutor_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    fecha: date
    horario: str | None = None
    descripcion: str
    estado: str
    comentarios: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class GuardiaFilterParams(BaseModel):
    """Parámetros de filtro para listado de guardias."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID | None = None
    tutor_id: UUID | None = None
    estado: str | None = None
    fecha_desde: date | None = None
    fecha_hasta: date | None = None


class PaginatedGuardiaResponse(BaseModel):
    """Respuesta paginada de guardias."""

    model_config = ConfigDict(extra="forbid")

    items: list[GuardiaRead]
    total: int
    limit: int
    offset: int


class ExportarGuardiasParams(BaseModel):
    """Parámetros de query para exportar guardias."""

    model_config = ConfigDict(extra="forbid")

    formato: str = Field(default="csv", pattern=r"^(csv|xlsx)$")
    materia_id: UUID | None = None
    tutor_id: UUID | None = None
    estado: str | None = None
    fecha_desde: date | None = None
    fecha_hasta: date | None = None
