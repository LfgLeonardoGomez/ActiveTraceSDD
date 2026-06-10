"""Schemas Pydantic para equipos docentes (C-08).

Todos los schemas tienen extra='forbid' (regla dura del proyecto).
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EquipoRead(BaseModel):
    """Schema de respuesta de equipo — asignación enriquecida con nombres."""

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
    # Nombres denormalizados del JOIN
    materia_nombre: str | None = None
    carrera_nombre: str | None = None
    cohorte_nombre: str | None = None
    usuario_nombre: str | None = None
    usuario_apellidos: str | None = None


class EquipoFilterParams(BaseModel):
    """Parámetros de filtro para listado de equipos."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    estado_vigencia: str | None = None


class PaginatedEquipoResponse(BaseModel):
    """Respuesta paginada de equipos."""

    model_config = ConfigDict(extra="forbid")

    items: list[EquipoRead]
    total: int
    limit: int
    offset: int


class AsignacionMasivaRequest(BaseModel):
    """Payload para asignación masiva de docentes."""

    model_config = ConfigDict(extra="forbid")

    usuario_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    rol: str = Field(..., min_length=1)
    desde: date
    hasta: date | None = None


class AsignacionMasivaResponse(BaseModel):
    """Respuesta de asignación masiva."""

    model_config = ConfigDict(extra="forbid")

    count: int
    created_ids: list[UUID]


class ClonarEquipoRequest(BaseModel):
    """Payload para clonación de equipo entre cohortes."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_id_origen: UUID
    cohorte_id_destino: UUID
    desde: date
    hasta: date | None = None
    preview: bool = False


class ClonarEquipoResponse(BaseModel):
    """Respuesta de clonación de equipo."""

    model_config = ConfigDict(extra="forbid")

    preview_count: int
    created_count: int | None = None
    created_ids: list[UUID] | None = None


class ActualizarVigenciaRequest(BaseModel):
    """Payload para actualizar vigencia de equipo."""

    model_config = ConfigDict(extra="forbid")

    desde: date
    hasta: date | None = None


class ActualizarVigenciaResponse(BaseModel):
    """Respuesta de actualización de vigencia."""

    model_config = ConfigDict(extra="forbid")

    count: int


class ExportarEquipoParams(BaseModel):
    """Parámetros de query para exportar equipo."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    format: str = Field(default="csv", pattern="^(csv|xlsx)$")
    include_pii: bool = False
