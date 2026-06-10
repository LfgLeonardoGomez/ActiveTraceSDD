"""Modelo ORM UmbralMateria (C-10).

E8 del modelo de datos: configuración de umbral de aprobación por asignación.

Reglas duras:
- FK a Asignacion garantiza que solo docentes realmente asignados pueden
  tener umbral (D-04 del design de C-10).
- valores_aprobatorios como JSONB (lista de strings) — D-05.
- Umbral aplica solo al scope del docente en esa materia (RN-04).
- unique constraint en (tenant_id, asignacion_id, materia_id) — un docente
  tiene un umbral por materia.
- Soft delete transversal via BaseModelMixin.
"""

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID

from app.core.database import Base
from app.models.mixins import BaseModelMixin

_DEFAULT_UMBRAL_PCT = 60
_DEFAULT_VALORES_APROBATORIOS = ["Satisfactorio", "Supera lo esperado"]


class UmbralMateria(BaseModelMixin, Base):
    """Umbral de aprobación de una materia por asignación docente.

    umbral_pct: porcentaje mínimo para nota numérica (defecto 60).
    valores_aprobatorios: lista JSONB de valores textuales aprobatorios
    (defecto: Satisfactorio, Supera lo esperado).
    """

    __tablename__ = "umbrales_materia"
    __table_args__ = (
        Index("ix_umbrales_materia_tenant_materia", "tenant_id", "materia_id"),
        Index("ix_umbrales_materia_asignacion", "asignacion_id"),
        UniqueConstraint(
            "tenant_id",
            "asignacion_id",
            "materia_id",
            name="uq_umbral_asignacion_materia",
        ),
    )

    asignacion_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("asignaciones.id", ondelete="RESTRICT"),
        nullable=False,
    )
    materia_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    umbral_pct: Mapped[int] = mapped_column(
        Integer, nullable=False, default=_DEFAULT_UMBRAL_PCT
    )
    valores_aprobatorios: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=lambda: list(_DEFAULT_VALORES_APROBATORIOS)
    )
