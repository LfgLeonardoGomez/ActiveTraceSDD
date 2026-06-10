"""Modelo ORM Calificacion (C-10).

E7 del modelo de datos: nota de un alumno en una actividad evaluable.

Reglas duras:
- aprobado es columna persistida, calculado al importar y recalculado en batch
  cuando cambia el umbral (D-01 del design de C-10).
- origen enum: Importado | Manual.
- Scope aislado: (tenant_id, usuario_importador_id, materia_id) — RN-04.
- Soft delete transversal via BaseModelMixin.
- unique constraint en (tenant_id, entrada_padron_id, materia_id, actividad,
  usuario_importador_id) — evita duplicados dentro del scope del docente.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class Calificacion(BaseModelMixin, Base):
    """Nota de un alumno (EntradaPadron) en una actividad de una materia.

    aprobado: derivado y persistido. True si nota_numerica >= umbral
    del docente, o si nota_textual está en valores_aprobatorios del umbral.
    Se recalcula en batch cuando el docente cambia su UmbralMateria.
    """

    __tablename__ = "calificaciones"
    __table_args__ = (
        Index("ix_calificaciones_tenant_materia", "tenant_id", "materia_id"),
        Index("ix_calificaciones_entrada_padron", "entrada_padron_id"),
        Index(
            "ix_calificaciones_scope",
            "tenant_id",
            "usuario_importador_id",
            "materia_id",
        ),
        UniqueConstraint(
            "tenant_id",
            "entrada_padron_id",
            "materia_id",
            "actividad",
            "usuario_importador_id",
            name="uq_calificacion_scope",
        ),
    )

    entrada_padron_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entradas_padron.id", ondelete="RESTRICT"),
        nullable=False,
    )
    materia_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Scope: docente que realizó la importación (RN-04)
    usuario_importador_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    actividad: Mapped[str] = mapped_column(String(255), nullable=False)
    nota_numerica: Mapped[float | None] = mapped_column(Float, nullable=True)
    nota_textual: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Derivado y persistido (D-01)
    aprobado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Importado | Manual
    origen: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Importado"
    )
    importado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
