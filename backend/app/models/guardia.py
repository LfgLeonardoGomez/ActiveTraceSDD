"""Modelo ORM Guardia (C-13).

Registro de una guardia de atención a alumnos, asignada a un tutor o docente.

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


class Guardia(BaseModelMixin, Base):
    """Guardia de atención a alumnos."""

    __tablename__ = "guardias"
    __table_args__ = (
        Index("ix_guardias_tenant_id", "tenant_id"),
        Index("ix_guardias_tutor_id", "tutor_id"),
        Index("ix_guardias_materia_id", "materia_id"),
        Index("ix_guardias_carrera_id", "carrera_id"),
        Index("ix_guardias_cohorte_id", "cohorte_id"),
    )

    tutor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    materia_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    carrera_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("carreras.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cohorte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    horario: Mapped[str | None] = mapped_column(String(11), nullable=True, default=None)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Pendiente",
        server_default="Pendiente",
    )
    comentarios: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Relaciones — lazy="raise"
    tutor: Mapped["Usuario"] = relationship(  # type: ignore[name-defined]
        "Usuario",
        foreign_keys=[tutor_id],
        back_populates=None,
        lazy="raise",
    )
    materia: Mapped["Materia"] = relationship(  # type: ignore[name-defined]
        "Materia",
        foreign_keys=[materia_id],
        back_populates=None,
        lazy="raise",
    )
    carrera: Mapped["Carrera"] = relationship(  # type: ignore[name-defined]
        "Carrera",
        foreign_keys=[carrera_id],
        back_populates=None,
        lazy="raise",
    )
    cohorte: Mapped["Cohorte"] = relationship(  # type: ignore[name-defined]
        "Cohorte",
        foreign_keys=[cohorte_id],
        back_populates=None,
        lazy="raise",
    )
