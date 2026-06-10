"""Modelo ORM InstanciaEncuentro (C-13).

Encuentro concreto, derivado de un slot o creado de forma independiente.

Reglas duras:
- tenant_id en cada tabla (aislamiento row-level)
- soft delete con deleted_at (nunca hard delete)
- lazy="raise" en relaciones async para evitar MissingGreenlet y N+1
"""

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class InstanciaEncuentro(BaseModelMixin, Base):
    """Instancia de encuentro concreto."""

    __tablename__ = "instancias_encuentro"
    __table_args__ = (
        Index("ix_instancias_encuentro_tenant_id", "tenant_id"),
        Index("ix_instancias_encuentro_slot_id", "slot_id"),
        Index("ix_instancias_encuentro_materia_id", "materia_id"),
        Index("ix_instancias_encuentro_fecha", "fecha"),
    )

    slot_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("slot_encuentros.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    materia_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    titulo: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[str] = mapped_column(String(5), nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Programado",
        server_default="Programado",
    )
    meet_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Relaciones — lazy="raise"
    slot: Mapped["SlotEncuentro | None"] = relationship(  # type: ignore[name-defined]
        "SlotEncuentro",
        foreign_keys=[slot_id],
        back_populates=None,
        lazy="raise",
    )
    materia: Mapped["Materia"] = relationship(  # type: ignore[name-defined]
        "Materia",
        foreign_keys=[materia_id],
        back_populates=None,
        lazy="raise",
    )
