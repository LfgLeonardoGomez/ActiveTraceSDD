"""Schemas Pydantic v2 para el módulo de padrón (C-09).

Todos los schemas tienen extra='forbid' (regla dura).
El email en EntradaPadronRead se devuelve en texto plano (descifrado en el repositorio).
El email no aparece en logs ni en schemas de listado masivo.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PadronImportRow(BaseModel):
    """Fila parseada de un archivo de padrón (sin persistir)."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    apellidos: str
    email: str
    comision: str = ""
    regional: str = ""


class PadronRowError(BaseModel):
    """Error de parseo en una fila específica del archivo."""

    model_config = ConfigDict(extra="forbid")

    fila: int
    mensaje: str


class PadronPreviewResponse(BaseModel):
    """Resultado del paso preview: resumen sin persistencia."""

    model_config = ConfigDict(extra="forbid")

    filas_validas: int
    filas_con_error: int
    columnas_detectadas: list[str]
    errores: list[PadronRowError]
    muestra: list[PadronImportRow] = Field(
        default_factory=list,
        description="Primeras N filas válidas para mostrar al usuario",
    )


class VersionPadronRead(BaseModel):
    """Respuesta de lectura de una versión del padrón."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    cargado_por: UUID
    cargado_at: datetime
    activa: bool
    origen: str
    created_at: datetime


class EntradaPadronRead(BaseModel):
    """Respuesta de lectura de una entrada del padrón.

    email se devuelve en texto plano (descifrado en PadronRepository).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    version_id: UUID
    usuario_id: UUID | None = None
    nombre: str
    apellidos: str
    email: str
    comision: str
    regional: str


class PadronConfirmResponse(BaseModel):
    """Respuesta tras confirmar la importación de un padrón."""

    model_config = ConfigDict(extra="forbid")

    version_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    filas_importadas: int
    activa: bool
    origen: str


class MoodleSyncRequest(BaseModel):
    """Request para sincronización on-demand con Moodle WS."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    course_id: str = Field(..., min_length=1, description="ID del curso en Moodle")
