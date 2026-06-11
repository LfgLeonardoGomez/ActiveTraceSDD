"""Schemas Pydantic para avisos y acknowledgment (C-15).

Todos los schemas usan extra='forbid' (regla dura del proyecto).
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AlcanceAviso(StrEnum):
    GLOBAL = "Global"
    POR_MATERIA = "PorMateria"
    POR_COHORTE = "PorCohorte"
    POR_ROL = "PorRol"


class SeveridadAviso(StrEnum):
    INFO = "Info"
    ADVERTENCIA = "Advertencia"
    CRITICO = "Crítico"


# ------------------------------------------------------------------
# Avisos CRUD
# ------------------------------------------------------------------

class AvisoCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alcance: AlcanceAviso
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    rol_destino: str | None = Field(default=None, max_length=30)
    severidad: SeveridadAviso
    titulo: str = Field(..., min_length=1, max_length=300)
    cuerpo: str = Field(..., min_length=1)
    inicio_en: datetime
    fin_en: datetime
    orden: int = Field(default=0, ge=0)
    activo: bool = True
    requiere_ack: bool = False


class AvisoUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alcance: AlcanceAviso | None = None
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    rol_destino: str | None = Field(default=None, max_length=30)
    severidad: SeveridadAviso | None = None
    titulo: str | None = Field(default=None, min_length=1, max_length=300)
    cuerpo: str | None = Field(default=None, min_length=1)
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = Field(default=None, ge=0)
    activo: bool | None = None
    requiere_ack: bool | None = None


class AvisoResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    alcance: AlcanceAviso
    materia_id: UUID | None
    cohorte_id: UUID | None
    rol_destino: str | None
    severidad: SeveridadAviso
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    created_at: datetime
    updated_at: datetime


class AvisoListResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AvisoResponseSchema]
    total: int
    page: int
    pages: int


# ------------------------------------------------------------------
# Avisos para usuario (mis-avisos)
# ------------------------------------------------------------------

class AvisoParaUsuarioSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    alcance: AlcanceAviso
    materia_id: UUID | None
    cohorte_id: UUID | None
    rol_destino: str | None
    severidad: SeveridadAviso
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    created_at: datetime
    updated_at: datetime
    acknowledged: bool


class AvisoParaUsuarioListSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AvisoParaUsuarioSchema]
    total: int
    page: int
    pages: int


# ------------------------------------------------------------------
# Acknowledgment
# ------------------------------------------------------------------

class AcknowledgmentResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    aviso_id: UUID
    usuario_id: UUID
    confirmado_at: datetime
    created_at: datetime
