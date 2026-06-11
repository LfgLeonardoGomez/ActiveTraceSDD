"""Modelos ORM para evaluaciones y coloquios (C-14).

E14 del modelo de datos: Evaluacion (convocatoria), ReservaEvaluacion (turno),
ResultadoEvaluacion (nota final). Tabla asociativa evaluacion_candidato
para el padrón de alumnos habilitados.

Reglas duras:
- Multi-tenant row-level: tenant_id en todas las entidades.
- Soft delete via BaseModelMixin (deleted_at).
- ReservaEvaluacion.estado: Activa | Cancelada.
- ResultadoEvaluacion.nota_final: texto libre (numérico o cualitativo).
- cupo_por_dia se valida a nivel aplicación con SELECT FOR UPDATE (D3).
"""

from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class TipoEvaluacion(StrEnum):
    PARCIAL = "Parcial"
    TP = "TP"
    COLOQUIO = "Coloquio"
    RECUPERATORIO = "Recuperatorio"


class EstadoReserva(StrEnum):
    ACTIVA = "Activa"
    CANCELADA = "Cancelada"


class Evaluacion(BaseModelMixin, Base):
    """Convocatoria de evaluación formal (coloquio, parcial, recuperatorio).

    dias_disponibles: ventana de inscripción en días.
    cupo_por_dia: máximo de reservas activas permitidas por día calendario.
    """

    __tablename__ = "evaluacion"
    __table_args__ = (
        Index("ix_evaluacion_tenant", "tenant_id"),
        Index("ix_evaluacion_materia", "tenant_id", "materia_id"),
        Index("ix_evaluacion_cohorte", "tenant_id", "cohorte_id"),
    )

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
    instancia: Mapped[str] = mapped_column(String(200), nullable=False)
    dias_disponibles: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cupo_por_dia: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class EvaluacionCandidato(Base):
    """Tabla asociativa: alumnos habilitados para una convocatoria.

    No extiende BaseModelMixin: es una relación pura (no tiene soft delete propio).
    El tenant_id está implícito por la FK a evaluacion.
    """

    __tablename__ = "evaluacion_candidato"
    __table_args__ = (
        UniqueConstraint(
            "evaluacion_id", "alumno_id", name="uq_evaluacion_candidato"
        ),
        Index("ix_evaluacion_candidato_evaluacion", "evaluacion_id"),
        Index("ix_evaluacion_candidato_alumno", "alumno_id"),
    )

    evaluacion_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluacion.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    alumno_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    )


class ReservaEvaluacion(BaseModelMixin, Base):
    """Reserva de turno de un alumno en una convocatoria.

    estado: Activa (cupo ocupado) | Cancelada (cupo liberado).
    Un alumno puede tener una sola ReservaEvaluacion Activa por convocatoria.
    """

    __tablename__ = "reserva_evaluacion"
    __table_args__ = (
        Index("ix_reserva_evaluacion_evaluacion", "evaluacion_id"),
        Index("ix_reserva_evaluacion_alumno", "alumno_id"),
        Index(
            "ix_reserva_evaluacion_tenant_estado",
            "tenant_id",
            "estado",
        ),
    )

    evaluacion_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluacion.id", ondelete="RESTRICT"),
        nullable=False,
    )
    alumno_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fecha_hora: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EstadoReserva.ACTIVA
    )


class ResultadoEvaluacion(BaseModelMixin, Base):
    """Resultado final de un alumno en una convocatoria.

    nota_final: texto libre — puede ser "7", "Aprobado", "Desaprobado", etc.
    No se deriva aprobado automáticamente (D4 del design).
    Upsert por (evaluacion_id, alumno_id).
    """

    __tablename__ = "resultado_evaluacion"
    __table_args__ = (
        UniqueConstraint(
            "evaluacion_id",
            "alumno_id",
            name="uq_resultado_evaluacion",
        ),
        Index("ix_resultado_evaluacion_evaluacion", "evaluacion_id"),
    )

    evaluacion_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evaluacion.id", ondelete="RESTRICT"),
        nullable=False,
    )
    alumno_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    nota_final: Mapped[str | None] = mapped_column(Text, nullable=True)
