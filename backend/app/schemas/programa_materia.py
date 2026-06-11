"""Schemas Pydantic para programas y fechas académicas (C-17).

Todos los schemas usan extra='forbid' (regla dura del proyecto).
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------------------------------------
# ProgramaMateria
# ------------------------------------------------------------------

class ProgramaMateriaCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str = Field(..., min_length=1, max_length=300)
    referencia_archivo: str = Field(..., min_length=1)


class ProgramaMateriaUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, min_length=1, max_length=300)
    referencia_archivo: str | None = Field(default=None, min_length=1)


class ProgramaMateriaResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str
    referencia_archivo: str
    cargado_at: datetime
    created_at: datetime
    updated_at: datetime


class ProgramaMateriaListResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProgramaMateriaResponseSchema]
    total: int
    page: int
    pages: int


# ------------------------------------------------------------------
# FechaAcademica
# ------------------------------------------------------------------

class FechaAcademicaCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    tipo: str = Field(..., min_length=1, max_length=30)
    numero: int = Field(..., ge=1)
    periodo: str = Field(..., min_length=1, max_length=20)
    fecha: date
    titulo: str = Field(..., min_length=1, max_length=300)


class FechaAcademicaUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo: str | None = Field(default=None, min_length=1, max_length=30)
    numero: int | None = Field(default=None, ge=1)
    periodo: str | None = Field(default=None, min_length=1, max_length=20)
    fecha: date | None = None
    titulo: str | None = Field(default=None, min_length=1, max_length=300)


class FechaAcademicaResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: str
    numero: int
    periodo: str
    fecha: date
    titulo: str
    created_at: datetime
    updated_at: datetime


class FechaAcademicaListResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[FechaAcademicaResponseSchema]
    total: int
    page: int
    pages: int


# ------------------------------------------------------------------
# Generación LMS
# ------------------------------------------------------------------

class LMSContentResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    html: str
    cantidad_fechas: int
