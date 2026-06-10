"""Modelo ORM Asignacion (C-07).

Vincula un Usuario con un Rol en un contexto académico con vigencia temporal.

Reglas duras:
- tenant_id en cada tabla (aislamiento row-level)
- soft delete con deleted_at (nunca hard delete)
- estado_vigencia es @property computado, NO columna de DB (D-03)
- lazy="raise" en relaciones async para evitar MissingGreenlet y N+1
- comisiones como ARRAY(Text) de PostgreSQL (D-04)
- responsable_id como FK self-referencial a usuarios.id (D-05)
"""

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class Asignacion(BaseModelMixin, Base):
    """Asignación de rol en contexto académico con vigencia temporal.

    Un usuario puede tener múltiples asignaciones simultáneas con distintos
    roles en distintos contextos académicos.

    estado_vigencia es calculado como @property:
    - "Vigente" si desde <= date.today() <= hasta (o hasta IS NULL)
    - "Vencida" en cualquier otro caso (incluye desde en el futuro)
    """

    __tablename__ = "asignaciones"
    __table_args__ = (
        Index("ix_asignaciones_tenant_id", "tenant_id"),
        Index("ix_asignaciones_usuario_id", "usuario_id"),
        Index("ix_asignaciones_materia_id", "materia_id"),
        Index("ix_asignaciones_carrera_id", "carrera_id"),
        Index("ix_asignaciones_responsable_id", "responsable_id"),
    )

    usuario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rol: Mapped[str] = mapped_column(Text, nullable=False)
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)

    # Contexto académico (todos opcionales — asignación global de tenant si son None)
    materia_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
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

    # Comisiones como ARRAY PostgreSQL (D-04)
    comisiones: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),
        nullable=True,
        default=list,
    )

    # Supervisor directo — FK self-referencial a usuarios.id (D-05)
    responsable_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # Relaciones — lazy="raise" para evitar N+1 en async (D-08)
    usuario: Mapped["Usuario"] = relationship(  # type: ignore[name-defined]
        "Usuario",
        foreign_keys=[usuario_id],
        back_populates=None,
        lazy="raise",
    )
    responsable: Mapped["Usuario | None"] = relationship(  # type: ignore[name-defined]
        "Usuario",
        foreign_keys=[responsable_id],
        back_populates=None,
        lazy="raise",
    )

    @property
    def estado_vigencia(self) -> str:
        """Calcula el estado de vigencia dinámicamente.

        Regla (D-03):
        - "Vigente" si desde <= date.today() Y (hasta IS NULL O date.today() <= hasta)
        - "Vencida" en cualquier otro caso (desde en el futuro, o hasta en el pasado)
        """
        today = date.today()
        if self.desde > today:
            return "Vencida"
        if self.hasta is not None and today > self.hasta:
            return "Vencida"
        return "Vigente"
