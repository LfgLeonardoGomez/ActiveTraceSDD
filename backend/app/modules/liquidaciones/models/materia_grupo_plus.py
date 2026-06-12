"""Modelo ORM MateriaGrupoPlus (C-18, decisión D1, PA-22).

Mapea cada materia del tenant a una clave de grupo de Plus con vigencia
temporal. Vive en el módulo de liquidaciones (no en estructura-academica)
porque el grupo es un atributo contable, no académico.

Preserva historial: al recategorizar una materia, se cierra la fila anterior
y se crea una nueva. Las liquidaciones cerradas reproducen el cálculo original.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class MateriaGrupoPlus(BaseModelMixin, Base):
    """Mapeo materia → grupo de Plus con vigencia temporal (PA-22).

    Invariante: no-solapamiento de (tenant_id, materia_id, [desde, hasta]).
    El solapamiento se valida en el service/repository (decisión D5).
    """

    __tablename__ = "materia_grupo_plus"
    __table_args__ = (
        Index("ix_mgp_tenant_materia_desde", "tenant_id", "materia_id", "desde"),
        Index("ix_mgp_tenant_grupo", "tenant_id", "grupo"),
    )

    materia_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    grupo: Mapped[str] = mapped_column(String(100), nullable=False)
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
