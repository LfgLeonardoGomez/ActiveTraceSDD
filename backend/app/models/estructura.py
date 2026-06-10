"""Modelos ORM para estructura académica (C-06).

Entidades: Carrera, Cohorte, Materia.

Reglas duras:
- tenant_id en cada tabla (aislamiento row-level)
- soft delete con deleted_at (nunca hard delete)
- estado (Activa/Inactiva) es atributo de ciclo de vida, independiente del soft delete
- lazy="raise" en relaciones async para evitar MissingGreenlet y N+1 (D-08)
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class Carrera(BaseModelMixin, Base):
    """Carrera académica del catálogo del tenant.

    Unicidad: (tenant_id, codigo) WHERE deleted_at IS NULL.
    """

    __tablename__ = "carreras"
    __table_args__ = (
        Index(
            "idx_carreras_tenant_codigo",
            "tenant_id",
            "codigo",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    codigo: Mapped[str] = mapped_column(Text, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Activa",
        server_default="Activa",
    )

    # Relación inversa a cohortes (lazy=raise: joins explícitos en repos)
    cohortes: Mapped[list["Cohorte"]] = relationship(
        "Cohorte",
        back_populates="carrera",
        lazy="raise",
    )


class Cohorte(BaseModelMixin, Base):
    """Cohorte de una carrera (año de inicio de cursado).

    Unicidad: (tenant_id, carrera_id, nombre) WHERE deleted_at IS NULL.
    Regla de negocio (D-04): no puede tener estado Activa si su Carrera es Inactiva.
    """

    __tablename__ = "cohortes"
    __table_args__ = (
        Index(
            "idx_cohortes_tenant_carrera_nombre",
            "tenant_id",
            "carrera_id",
            "nombre",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    carrera_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("carreras.id", ondelete="RESTRICT"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Activa",
        server_default="Activa",
    )

    # Relación a Carrera — lazy=raise fuerza joins explícitos (D-08)
    carrera: Mapped["Carrera"] = relationship(
        "Carrera",
        back_populates="cohortes",
        lazy="raise",
    )


class Materia(BaseModelMixin, Base):
    """Materia del catálogo del tenant.

    Unicidad: (tenant_id, codigo) WHERE deleted_at IS NULL.
    """

    __tablename__ = "materias"
    __table_args__ = (
        Index(
            "idx_materias_tenant_codigo",
            "tenant_id",
            "codigo",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    codigo: Mapped[str] = mapped_column(Text, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Activa",
        server_default="Activa",
    )
