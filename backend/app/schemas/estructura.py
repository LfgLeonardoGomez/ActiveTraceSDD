"""Schemas Pydantic para estructura académica (C-06).

DTOs para Carrera, Cohorte, Materia.
Todos usan extra='forbid' (regla dura del proyecto).
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ----------------------------------------------------------------
# Carrera
# ----------------------------------------------------------------


class CarreraCreate(BaseModel):
    """Datos para crear una carrera."""

    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str
    estado: str = "Activa"


class CarreraUpdate(BaseModel):
    """Actualización parcial de carrera (todos los campos opcionales)."""

    model_config = ConfigDict(extra="forbid")

    codigo: str | None = None
    nombre: str | None = None
    estado: str | None = None


class CarreraRead(BaseModel):
    """Respuesta de carrera."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    codigo: str
    nombre: str
    estado: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


# ----------------------------------------------------------------
# Cohorte
# ----------------------------------------------------------------


class CohorteCreate(BaseModel):
    """Datos para crear una cohorte."""

    model_config = ConfigDict(extra="forbid")

    carrera_id: UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None = None
    estado: str = "Activa"


class CohorteUpdate(BaseModel):
    """Actualización parcial de cohorte (todos los campos opcionales)."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    anio: int | None = None
    vig_desde: date | None = None
    vig_hasta: date | None = None
    estado: str | None = None


class CohorteRead(BaseModel):
    """Respuesta de cohorte."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    carrera_id: UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None = None
    estado: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


# ----------------------------------------------------------------
# Materia
# ----------------------------------------------------------------


class MateriaCreate(BaseModel):
    """Datos para crear una materia."""

    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str
    estado: str = "Activa"


class MateriaUpdate(BaseModel):
    """Actualización parcial de materia (todos los campos opcionales)."""

    model_config = ConfigDict(extra="forbid")

    codigo: str | None = None
    nombre: str | None = None
    estado: str | None = None


class MateriaRead(BaseModel):
    """Respuesta de materia."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    codigo: str
    nombre: str
    estado: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


# ----------------------------------------------------------------
# Respuestas paginadas
# ----------------------------------------------------------------


class PaginatedCarrerasResponse(BaseModel):
    """Respuesta paginada de carreras."""

    model_config = ConfigDict(extra="forbid")

    items: list[CarreraRead]
    total: int
    limit: int
    offset: int


class PaginatedCohortesResponse(BaseModel):
    """Respuesta paginada de cohortes."""

    model_config = ConfigDict(extra="forbid")

    items: list[CohorteRead]
    total: int
    limit: int
    offset: int


class PaginatedMateriasResponse(BaseModel):
    """Respuesta paginada de materias."""

    model_config = ConfigDict(extra="forbid")

    items: list[MateriaRead]
    total: int
    limit: int
    offset: int
