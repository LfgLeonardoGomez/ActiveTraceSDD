"""Modelos ORM para programas y fechas académicas (C-17).

Entidades: ProgramaMateria, FechaAcademica.

Reglas duras:
- tenant_id en cada tabla (aislamiento row-level)
- soft delete con deleted_at (nunca hard delete)
- ProgramaMateria: unicidad (tenant_id, materia_id, carrera_id, cohorte_id) WHERE deleted_at IS NULL
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class ProgramaMateria(BaseModelMixin, Base):
    """Documento oficial de programa de una materia para una carrera y cohorte.

    Unicidad: (tenant_id, materia_id, carrera_id, cohorte_id) WHERE deleted_at IS NULL.
    """

    __tablename__ = "programa_materia"
    __table_args__ = (
        Index(
            "idx_programa_materia_combinacion",
            "tenant_id",
            "materia_id",
            "carrera_id",
            "cohorte_id",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
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
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    referencia_archivo: Mapped[str] = mapped_column(Text, nullable=False)
    cargado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(),
    )


class FechaAcademica(BaseModelMixin, Base):
    """Calendarización de instancias evaluativas dentro de un período académico.

    Tipo: Parcial | TP | Coloquio | Recuperatorio.
    """

    __tablename__ = "fecha_academica"

    materia_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cohorte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
