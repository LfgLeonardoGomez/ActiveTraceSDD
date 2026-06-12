"""Modelo ORM SalarioPlus (C-18).

Define el monto plus por (grupo × rol) con vigencia temporal y tope de
acumulación opcional (decisión D2, PA-23).

tope_acumulacion: DECIMAL NULLABLE.
  - NULL = sin tope (acumulación ilimitada).
  - > 0 = máximo de comisiones del grupo que acumulan plus para el docente.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class SalarioPlus(BaseModelMixin, Base):
    """Monto plus de honorarios por (grupo × rol) con vigencia temporal.

    Invariante: no-solapamiento de (tenant_id, grupo, rol, [desde, hasta]).
    El solapamiento se valida en el service/repository (decisión D5).
    """

    __tablename__ = "salarios_plus"
    __table_args__ = (
        Index("ix_salarios_plus_tenant_grupo_rol_desde", "tenant_id", "grupo", "rol", "desde"),
    )

    grupo: Mapped[str] = mapped_column(String(100), nullable=False)
    rol: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tope_acumulacion: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        default=None,
        comment="NULL = sin tope. Positivo = máximo de comisiones del grupo que acumulan plus.",
    )
    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
