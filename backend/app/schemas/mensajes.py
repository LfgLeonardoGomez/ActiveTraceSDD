"""Schemas Pydantic para mensajería interna (C-20).

Reglas duras:
- extra='forbid' en todo schema.
- from_attributes=True en schemas de lectura.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MensajeRead(BaseModel):
    """Schema para lectura de un mensaje."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID
    remitente_id: UUID
    asunto: str
    cuerpo: str
    created_at: datetime


class InboxThreadRead(BaseModel):
    """Schema para listado de threads (root messages) en inbox."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID
    remitente_id: UUID
    asunto: str
    cuerpo: str
    created_at: datetime


class InboxThreadDetailRead(BaseModel):
    """Schema para detalle de thread con replies."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID
    remitente_id: UUID
    asunto: str
    cuerpo: str
    created_at: datetime
    replies: list[MensajeRead]


class MensajeReplyCreate(BaseModel):
    """Schema para crear una respuesta en un thread."""

    model_config = ConfigDict(extra="forbid")

    asunto: str | None = None
    cuerpo: str
