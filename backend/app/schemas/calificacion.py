"""Schemas Pydantic v2 para el módulo de calificaciones (C-10).

Todos los schemas tienen extra='forbid' (regla dura).
Flujo preview/confirm: el cliente sube el archivo dos veces (D-03 del design).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ActividadDetectada(BaseModel):
    """Actividad detectada en el archivo LMS durante el preview."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    tipo: str  # "numerica" | "textual"
    total_alumnos: int
    alumnos_con_valor: int


class AlumnoFila(BaseModel):
    """Fila de alumno extraída del archivo LMS."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID | None = None
    nombre: str
    apellidos: str
    actividades: dict[str, str | float | None] = Field(
        default_factory=dict,
        description="actividad -> valor (str o float o null)",
    )


class ImportPreviewResponse(BaseModel):
    """Resultado del preview: lista de actividades detectadas y alumnos."""

    model_config = ConfigDict(extra="forbid")

    actividades: list[ActividadDetectada]
    total_alumnos: int
    advertencias: list[str] = Field(default_factory=list)


class ImportConfirmRequest(BaseModel):
    """Request de confirmación de importación: qué actividades incluir."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    actividades_seleccionadas: list[str] = Field(
        min_length=1,
        description="Nombres de actividades a persistir (deben estar en el preview)",
    )


class ImportConfirmResponse(BaseModel):
    """Resultado de la importación confirmada."""

    model_config = ConfigDict(extra="forbid")

    filas_importadas: int
    actividades_incluidas: int
    alumnos_actualizados: int


class CalificacionRead(BaseModel):
    """Lectura de una calificación persistida."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    entrada_padron_id: UUID
    materia_id: UUID
    usuario_importador_id: UUID
    actividad: str
    nota_numerica: float | None
    nota_textual: str | None
    aprobado: bool
    origen: str
    importado_at: datetime
