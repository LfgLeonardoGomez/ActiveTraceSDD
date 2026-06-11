"""Schemas Pydantic para evaluaciones y coloquios (C-14).

Todos los schemas usan extra='forbid' (regla dura).
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TipoEvaluacion(StrEnum):
    PARCIAL = "Parcial"
    TP = "TP"
    COLOQUIO = "Coloquio"
    RECUPERATORIO = "Recuperatorio"


class EstadoReserva(StrEnum):
    ACTIVA = "Activa"
    CANCELADA = "Cancelada"


# ------------------------------------------------------------------
# Convocatorias
# ------------------------------------------------------------------

class EvaluacionCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    tipo: TipoEvaluacion
    instancia: str = Field(..., min_length=1, max_length=200)
    dias_disponibles: int = Field(default=1, ge=1)
    cupo_por_dia: int = Field(default=1, ge=1)


class EvaluacionUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instancia: str | None = Field(default=None, min_length=1, max_length=200)
    dias_disponibles: int | None = Field(default=None, ge=1)
    cupo_por_dia: int | None = Field(default=None, ge=1)


class EvaluacionResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: TipoEvaluacion
    instancia: str
    dias_disponibles: int
    cupo_por_dia: int
    convocados: int
    reservas_activas: int
    cupos_libres_por_dia: int
    created_at: datetime


# ------------------------------------------------------------------
# Candidatos
# ------------------------------------------------------------------

class CandidatosImportSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_ids: list[UUID] = Field(..., min_length=1)


class CandidatosImportResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_candidatos: int


class CandidatoItemSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_id: UUID
    alumno_nombre: str
    alumno_email: str


# ------------------------------------------------------------------
# Reservas
# ------------------------------------------------------------------

class ReservaCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha_hora: datetime


class ReservaResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    alumno_nombre: str
    fecha_hora: datetime
    estado: EstadoReserva
    created_at: datetime


class ReservasListResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ReservaResponseSchema]
    total: int
    page: int
    pages: int


# ------------------------------------------------------------------
# Resultados
# ------------------------------------------------------------------

class ResultadoUpsertSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_id: UUID
    nota_final: str = Field(..., min_length=1, max_length=200)


class ResultadoResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_id: UUID
    alumno_nombre: str
    alumno_email: str
    nota_final: str | None


class ResultadosListResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ResultadoResponseSchema]
    total: int
    page: int
    pages: int


# ------------------------------------------------------------------
# Métricas globales y agenda
# ------------------------------------------------------------------

class MetricasColoquiosSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_alumnos_cargados: int
    instancias_activas: int
    reservas_activas: int
    notas_registradas: int


class AgendaItemSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reserva_id: UUID
    evaluacion_id: UUID
    materia_id: UUID
    materia_nombre: str
    instancia: str
    alumno_id: UUID
    alumno_nombre: str
    fecha_hora: datetime
    estado: EstadoReserva


class AgendaResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AgendaItemSchema]
    total: int
    page: int
    pages: int
