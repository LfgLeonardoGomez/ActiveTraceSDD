"""Schemas Pydantic para el módulo de análisis de atrasados y reportes (C-11).

Todos los schemas usan extra='forbid' (regla dura del proyecto).
"""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class MotivoAtrasado(str, Enum):
    """Motivo por el que un alumno se considera atrasado."""

    sin_datos = "sin_datos"
    nota_insuficiente = "nota_insuficiente"
    actividades_faltantes = "actividades_faltantes"


class EstadoAlumno(str, Enum):
    """Estado del alumno en el monitor de seguimiento."""

    al_dia = "al_dia"
    atrasado = "atrasado"
    sin_datos = "sin_datos"


# ---------------------------------------------------------------------------
# Análisis de atrasados
# ---------------------------------------------------------------------------


class AlumnoAtrasadoSchema(BaseModel):
    """Alumno que aparece en la lista de atrasados de una asignación."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID
    alumno_nombre: str
    alumno_email: str
    motivo: MotivoAtrasado
    actividades_faltantes_count: int
    actividades_reprobadas_count: int


class AtrasadosResponseSchema(BaseModel):
    """Respuesta paginada de alumnos atrasados."""

    model_config = ConfigDict(extra="forbid")

    items: list[AlumnoAtrasadoSchema]
    total: int
    page: int
    pages: int


# ---------------------------------------------------------------------------
# Ranking de actividades aprobadas
# ---------------------------------------------------------------------------


class RankingItemSchema(BaseModel):
    """Entrada en el ranking de actividades aprobadas."""

    model_config = ConfigDict(extra="forbid")

    posicion: int
    entrada_padron_id: UUID
    alumno_nombre: str
    actividades_aprobadas: int


class RankingResponseSchema(BaseModel):
    """Respuesta de ranking completa (sin paginación)."""

    model_config = ConfigDict(extra="forbid")

    items: list[RankingItemSchema]
    total: int


# ---------------------------------------------------------------------------
# Reporte rápido de métricas
# ---------------------------------------------------------------------------


class ReporteRapidoSchema(BaseModel):
    """Métricas consolidadas de una asignación."""

    model_config = ConfigDict(extra="forbid")

    total_alumnos: int
    total_actividades: int
    con_aprobadas: int
    atrasados: int
    pct_aprobacion: float
    sin_datos: bool


# ---------------------------------------------------------------------------
# Notas finales
# ---------------------------------------------------------------------------


class NotaFinalItemSchema(BaseModel):
    """Nota final calculada para un alumno."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID
    alumno_nombre: str
    alumno_email: str
    nota_final: float | None


# ---------------------------------------------------------------------------
# Monitor de seguimiento
# ---------------------------------------------------------------------------


class MonitorItemSchema(BaseModel):
    """Fila del monitor de seguimiento."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID
    alumno_nombre: str
    email: str
    materia_id: UUID
    materia_nombre: str
    actividades_aprobadas: int
    actividades_totales: int
    estado: EstadoAlumno


class MonitorResponseSchema(BaseModel):
    """Respuesta paginada del monitor de seguimiento."""

    model_config = ConfigDict(extra="forbid")

    items: list[MonitorItemSchema]
    total: int
    page: int
    pages: int
