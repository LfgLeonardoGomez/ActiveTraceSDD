"""Modelo Comunicacion — E-21: mensajes salientes con ciclo de vida controlado.

Estados: Pendiente → Enviando → Enviado | Error | Cancelado
- Solo transiciones válidas permitidas (máquina de estados en capa Service).
- destinatario cifrado AES-256 en reposo (nunca en texto plano).
- aprobado=True requerido para despacho cuando Tenant.requiere_aprobacion=True.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class EstadoComunicacion(str, Enum):
    """Estados posibles de una comunicación saliente."""

    pendiente = "Pendiente"
    enviando = "Enviando"
    enviado = "Enviado"
    error = "Error"
    cancelado = "Cancelado"


# Transiciones válidas de estado (máquina de estados)
TRANSICIONES_VALIDAS: dict[EstadoComunicacion, set[EstadoComunicacion]] = {
    EstadoComunicacion.pendiente: {EstadoComunicacion.enviando, EstadoComunicacion.cancelado},
    EstadoComunicacion.enviando: {EstadoComunicacion.enviado, EstadoComunicacion.error},
    EstadoComunicacion.enviado: set(),       # estado terminal
    EstadoComunicacion.error: {EstadoComunicacion.pendiente},  # retry manual
    EstadoComunicacion.cancelado: set(),     # estado terminal
}


def transicion_valida(desde: EstadoComunicacion, hasta: EstadoComunicacion) -> bool:
    """Verifica si la transición de estado es válida."""
    return hasta in TRANSICIONES_VALIDAS.get(desde, set())


class Comunicacion(Base, BaseModelMixin):
    """Mensaje saliente (email vía N8N) con ciclo de vida completo.

    Campos E-21:
        id, tenant_id: heredados de BaseModelMixin.
        enviado_por: FK al usuario que encoló el mensaje.
        materia_id: FK lógica a materias (sin FK constraint por independencia).
        destinatario: email cifrado AES-256 (nunca en texto plano).
        asunto: asunto del mensaje.
        cuerpo: cuerpo del mensaje.
        estado: ciclo de vida (Pendiente/Enviando/Enviado/Error/Cancelado).
        lote_id: UUID compartido por todos los mensajes del mismo encolado.
        aprobado: True si fue aprobado para despacho (usado cuando tenant requiere aprobación).
        enviado_at: timestamp de despacho exitoso.
        error_detalle: descripción del error si estado=Error.
        deleted_at: heredado de BaseModelMixin (soft delete).
    """

    __tablename__ = "comunicacion"

    enviado_por: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    materia_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    # destinatario cifrado AES-256 — NUNCA en texto plano
    destinatario: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    asunto: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    cuerpo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EstadoComunicacion.pendiente.value,
    )
    lote_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        default=uuid4,
    )
    aprobado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    enviado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    error_detalle: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
