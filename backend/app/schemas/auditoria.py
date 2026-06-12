"""Schemas Pydantic para el módulo de auditoría y métricas (C-19).

Todos los schemas usan extra='forbid' (regla dura del proyecto).
Read-only DTOs — no se expone ninguna operación de escritura.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Schemas de panel (F9.1)
# ---------------------------------------------------------------------------


class RangoFechasResponse(BaseModel):
    """Rango de fechas aplicado en la consulta (inclusive)."""

    model_config = ConfigDict(extra="forbid")

    desde: datetime
    hasta: datetime


class AccionesPorDiaItem(BaseModel):
    """Conteo de acciones de auditoría por día."""

    model_config = ConfigDict(extra="forbid")

    fecha: date
    total: int


class AccionesPorDiaResponse(BaseModel):
    """Respuesta del sub-panel acciones-por-dia."""

    model_config = ConfigDict(extra="forbid")

    items: list[AccionesPorDiaItem]
    rango: RangoFechasResponse


class ConteoEstadosComunicacion(BaseModel):
    """Conteo de comunicaciones por estado para un docente."""

    model_config = ConfigDict(extra="forbid")

    Pendiente: int = 0
    Enviando: int = 0
    Enviado: int = 0
    Error: int = 0
    Cancelado: int = 0


class ComunicacionesPorDocenteItem(BaseModel):
    """Agregado de comunicaciones de un docente."""

    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    usuario_nombre: str
    conteos: ConteoEstadosComunicacion


class ComunicacionesPorDocenteResponse(BaseModel):
    """Respuesta del sub-panel comunicaciones-por-docente."""

    model_config = ConfigDict(extra="forbid")

    items: list[ComunicacionesPorDocenteItem]


class InteraccionesPorDocenteMateriaItem(BaseModel):
    """Conteo de interacciones por (docente, materia, accion)."""

    model_config = ConfigDict(extra="forbid")

    actor_id: UUID
    actor_nombre: str
    materia_id: UUID | None
    materia_nombre: str | None
    accion: str
    categoria: str
    total: int


class InteraccionesPorDocenteMateriaResponse(BaseModel):
    """Respuesta del sub-panel interacciones-por-docente-materia."""

    model_config = ConfigDict(extra="forbid")

    items: list[InteraccionesPorDocenteMateriaItem]


class UltimaAccionItem(BaseModel):
    """Item del log de últimas acciones del panel."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    fecha_hora: datetime
    actor_id: UUID
    impersonado_id: UUID | None
    materia_id: UUID | None
    accion: str
    categoria: str
    filas_afectadas: int
    ip: str | None
    user_agent: str | None


class UltimasAccionesResponse(BaseModel):
    """Respuesta del sub-panel ultimas-acciones."""

    model_config = ConfigDict(extra="forbid")

    items: list[UltimaAccionItem]


# ---------------------------------------------------------------------------
# Schemas de log completo de auditoría (F9.2)
# ---------------------------------------------------------------------------


class AuditLogEntrySchema(BaseModel):
    """Entrada completa del log de auditoría (incluye detalle JSONB)."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    fecha_hora: datetime
    actor_id: UUID
    impersonado_id: UUID | None
    materia_id: UUID | None
    accion: str
    categoria: str
    filas_afectadas: int
    ip: str | None
    user_agent: str | None
    detalle: dict | None


class AuditLogPageResponse(BaseModel):
    """Respuesta paginada del log completo de auditoría."""

    model_config = ConfigDict(extra="forbid")

    items: list[AuditLogEntrySchema]
    total: int
    page: int
    pages: int


# ---------------------------------------------------------------------------
# Schema catálogo de acciones
# ---------------------------------------------------------------------------


class CatalogoAccionItem(BaseModel):
    """Código de acción con su categoría derivada del prefijo."""

    model_config = ConfigDict(extra="forbid")

    codigo: str
    categoria: str


class CatalogoAccionesResponse(BaseModel):
    """Catálogo completo de códigos de acción (enum AuditAction)."""

    model_config = ConfigDict(extra="forbid")

    items: list[CatalogoAccionItem]
