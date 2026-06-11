"""Modelos ORM para tareas internas y comentarios (C-16).

E12 + FL-05 reconciliación: Tarea con estado machine, criterio_cierre,
aprobada/devuelta flags, y ComentarioTarea con soft delete.

Reglas duras:
- Multi-tenant row-level: tenant_id en todas las entidades.
- Soft delete via BaseModelMixin (deleted_at).
- contexto_id es opaque UUID — sin FK.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class EstadoTarea(StrEnum):
    """Estados del ciclo de vida de una tarea interna."""

    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    RESUELTA = "Resuelta"
    CANCELADA = "Cancelada"


class Tarea(BaseModelMixin, Base):
    """Tarea interna asignada entre coordinadores y docentes.

    Flujo: Pendiente → En progreso → Resuelta → (aprobada/cerrada).
    Puede ser devuelta a En progreso para rework.
    """

    __tablename__ = "tarea"
    __table_args__ = (
        Index("ix_tarea_tenant_estado", "tenant_id", "estado"),
        Index("ix_tarea_asignado_estado", "tenant_id", "asignado_a", "estado"),
        Index("ix_tarea_materia", "tenant_id", "materia_id"),
    )

    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    criterio_cierre: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=EstadoTarea.PENDIENTE,
    )
    aprobada: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    devuelta: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    asignado_a: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    asignado_por: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revisada_por: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    revisada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    materia_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="SET NULL"),
        nullable=True,
    )
    contexto_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )


class ComentarioTarea(BaseModelMixin, Base):
    """Comentario sobre una tarea interna.

    Soft delete via BaseModelMixin. Carga por tarea_id indexada.
    """

    __tablename__ = "comentario_tarea"
    __table_args__ = (
        Index("ix_comentario_tarea_tarea", "tarea_id"),
    )

    tarea_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tarea.id", ondelete="CASCADE"),
        nullable=False,
    )
    autor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
