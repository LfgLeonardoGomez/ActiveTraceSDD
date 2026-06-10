"""Schemas Pydantic para encuentros y slots (C-13).

Todos los schemas tienen extra='forbid' (regla dura del proyecto).
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ------------------------------------------------------------------
# Slot schemas
# ------------------------------------------------------------------

class SlotCreate(BaseModel):
    """Schema para crear un slot de encuentro recurrente."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    titulo: str = Field(..., min_length=1)
    dia_semana: int = Field(..., ge=0, le=6)
    hora: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    fecha_inicio: date
    cant_semanas: int = Field(..., ge=1, le=52)
    meet_url: str | None = Field(None, max_length=2048)
    vigencia: str | None = None


class SlotUpdate(BaseModel):
    """Schema para actualización parcial de slot."""

    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(None, min_length=1)
    meet_url: str | None = Field(None, max_length=2048)
    vigencia: str | None = None


class SlotRead(BaseModel):
    """Schema de respuesta de slot."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID
    tenant_id: UUID
    creador_id: UUID
    materia_id: UUID
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    titulo: str
    dia_semana: int
    hora: str
    fecha_inicio: date
    cant_semanas: int
    meet_url: str | None = None
    vigencia: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PaginatedSlotResponse(BaseModel):
    """Respuesta paginada de slots."""

    model_config = ConfigDict(extra="forbid")

    items: list[SlotRead]
    total: int
    limit: int
    offset: int


# ------------------------------------------------------------------
# Instancia schemas
# ------------------------------------------------------------------

class InstanciaCreate(BaseModel):
    """Schema para crear una instancia de encuentro (única o vinculada a slot)."""

    model_config = ConfigDict(extra="forbid")

    slot_id: UUID | None = None
    materia_id: UUID
    titulo: str | None = None
    fecha: date
    hora: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    meet_url: str | None = Field(None, max_length=2048)


class InstanciaUpdate(BaseModel):
    """Schema para actualización parcial de instancia."""

    model_config = ConfigDict(extra="forbid")

    estado: str | None = Field(None, pattern=r"^(Programado|Realizado|Cancelado)$")
    meet_url: str | None = Field(None, max_length=2048)
    video_url: str | None = Field(None, max_length=2048)
    comentario: str | None = None


class InstanciaRead(BaseModel):
    """Schema de respuesta de instancia de encuentro."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID
    tenant_id: UUID
    slot_id: UUID | None = None
    materia_id: UUID
    titulo: str | None = None
    fecha: date
    hora: str
    estado: str
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class InstanciaFilterParams(BaseModel):
    """Parámetros de filtro para listado de instancias."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID | None = None
    slot_id: UUID | None = None
    estado: str | None = None
    fecha_desde: date | None = None
    fecha_hasta: date | None = None


class PaginatedInstanciaResponse(BaseModel):
    """Respuesta paginada de instancias."""

    model_config = ConfigDict(extra="forbid")

    items: list[InstanciaRead]
    total: int
    limit: int
    offset: int


# ------------------------------------------------------------------
# Bloque HTML / Markdown
# ------------------------------------------------------------------

class BloqueHtmlParams(BaseModel):
    """Parámetros para generar bloque HTML o Markdown."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    slot_id: UUID | None = None
    formato: str = Field(default="html", pattern=r"^(html|markdown)$")
