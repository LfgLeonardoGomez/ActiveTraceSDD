"""Schemas Pydantic para el módulo de comunicaciones (C-12).

Todos los schemas usan extra='forbid' (regla dura del proyecto).
Nota de seguridad: destinatario NUNCA aparece en schemas de respuesta ni logs.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Sub-schema: destinatario individual
# ---------------------------------------------------------------------------


class DestinatarioSchema(BaseModel):
    """Destinatario individual para preview o encolado.

    Nota: email es texto plano en request (se cifra al persistir en el repository).
    """

    model_config = ConfigDict(extra="forbid")

    alumno_id: UUID
    nombre: str
    email: str = Field(..., description="Email en texto plano (se cifra al persistir)")


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


class ComunicacionPreviewRequestSchema(BaseModel):
    """Solicitud de preview de mensaje sin persistencia."""

    model_config = ConfigDict(extra="forbid")

    destinatarios: list[DestinatarioSchema]
    plantilla_asunto: str
    plantilla_cuerpo: str


class ComunicacionPreviewItemSchema(BaseModel):
    """Resultado de preview para un destinatario."""

    model_config = ConfigDict(extra="forbid")

    alumno_id: UUID
    asunto_renderizado: str
    cuerpo_renderizado: str


# ---------------------------------------------------------------------------
# Encolado de lote
# ---------------------------------------------------------------------------


class ComunicacionLoteRequestSchema(BaseModel):
    """Solicitud de encolado masivo de comunicaciones."""

    model_config = ConfigDict(extra="forbid")

    destinatarios: list[DestinatarioSchema]
    plantilla_asunto: str
    plantilla_cuerpo: str
    materia_id: UUID


class ComunicacionLoteResponseSchema(BaseModel):
    """Respuesta al encolar un lote de comunicaciones."""

    model_config = ConfigDict(extra="forbid")

    lote_id: UUID
    total_encolados: int
    requiere_aprobacion: bool


# ---------------------------------------------------------------------------
# Estado de lote
# ---------------------------------------------------------------------------


class LoteEstadoSchema(BaseModel):
    """Estado agregado de un lote de comunicaciones."""

    model_config = ConfigDict(extra="forbid")

    lote_id: UUID
    total: int
    pendiente: int
    enviando: int
    enviado: int
    error: int
    cancelado: int
