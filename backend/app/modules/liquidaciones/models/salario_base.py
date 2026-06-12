"""Modelo ORM SalarioBase (C-18).

Define el monto base de honorarios por rol docente con vigencia temporal.
Una sola fila activa por (tenant_id, rol) en cada instante.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class SalarioBase(BaseModelMixin, Base):
    """Monto base de honorarios por rol docente con vigencia temporal.

    Invariante: no-solapamiento de (tenant_id, rol, [desde, hasta]).
    El solapamiento se valida en el service/repository (decisión D5).
    """

    __tablename__ = "salarios_base"
    __table_args__ = (
        Index("ix_salarios_base_tenant_rol_desde", "tenant_id", "rol", "desde"),
    )

    rol: Mapped[str] = mapped_column(String(50), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
