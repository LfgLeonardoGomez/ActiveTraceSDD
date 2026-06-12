"""Modelo Mensaje para mensajería interna entre usuarios (C-20).

Reglas duras:
- parent_id es self-referencing FK nullable para threading.
- remitente_id y destinatario_id son FK a usuarios.id.
- tenant_id heredado de BaseModelMixin.
- Soft delete via deleted_at.
"""

from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class Mensaje(BaseModelMixin, Base):
    """Mensaje interno entre usuarios del mismo tenant."""

    __tablename__ = "mensaje"
    __table_args__ = (
        Index(
            "ix_mensaje_tenant_destinatario_parent_deleted",
            "tenant_id",
            "destinatario_id",
            "parent_id",
            "deleted_at",
        ),
        Index(
            "ix_mensaje_tenant_parent_created",
            "tenant_id",
            "parent_id",
            "created_at",
        ),
    )

    remitente_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    destinatario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    asunto: Mapped[str] = mapped_column(String(500), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("mensaje.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
    )


