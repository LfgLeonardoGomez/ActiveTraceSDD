"""Modelo ORM SlotEncuentro (C-13).

Plantilla que define la recurrencia de un encuentro sincrónico.

Reglas duras:
- tenant_id en cada tabla (aislamiento row-level)
- soft delete con deleted_at (nunca hard delete)
- lazy="raise" en relaciones async para evitar MissingGreenlet y N+1
"""

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class SlotEncuentro(BaseModelMixin, Base):
    """Slot de encuentro recurrente."""

    __tablename__ = "slot_encuentros"
    __table_args__ = (
        Index("ix_slot_encuentros_tenant_id", "tenant_id"),
        Index("ix_slot_encuentros_materia_id", "materia_id"),
        Index("ix_slot_encuentros_carrera_id", "carrera_id"),
        Index("ix_slot_encuentros_cohorte_id", "cohorte_id"),
        Index("ix_slot_encuentros_creador_id", "creador_id"),
    )

    creador_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    materia_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    carrera_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("carreras.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    cohorte_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    dia_semana: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    hora: Mapped[str] = mapped_column(String(5), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    cant_semanas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    meet_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    vigencia: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Relaciones — lazy="raise" para evitar N+1 en async
    creador: Mapped["Usuario"] = relationship(  # type: ignore[name-defined]
        "Usuario",
        foreign_keys=[creador_id],
        back_populates=None,
        lazy="raise",
    )
    materia: Mapped["Materia"] = relationship(  # type: ignore[name-defined]
        "Materia",
        foreign_keys=[materia_id],
        back_populates=None,
        lazy="raise",
    )
    carrera: Mapped["Carrera | None"] = relationship(  # type: ignore[name-defined]
        "Carrera",
        foreign_keys=[carrera_id],
        back_populates=None,
        lazy="raise",
    )
    cohorte: Mapped["Cohorte | None"] = relationship(  # type: ignore[name-defined]
        "Cohorte",
        foreign_keys=[cohorte_id],
        back_populates=None,
        lazy="raise",
    )
