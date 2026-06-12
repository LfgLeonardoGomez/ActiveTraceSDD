"""Modelo ORM Liquidacion (C-18).

Fila de liquidación de honorarios por (usuario, rol, cohorte, periodo).
El estado Cerrada es inmutable (D3): el repository rechaza toda mutación.

Mientras estado=Abierta: los montos se recalculan on-demand (D4).
Cuando se cierra: los montos se persisten y la fila queda frozen.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin
from app.modules.liquidaciones.models.enums import EstadoLiquidacion


class Liquidacion(BaseModelMixin, Base):
    """Fila de liquidación de honorarios (C-18).

    estado=Cerrada → inmutable desde repository.
    excluido_por_factura: snapshot del flag facturador al momento del cierre.
    """

    __tablename__ = "liquidaciones"
    __table_args__ = (
        Index(
            "ix_liquidaciones_tenant_cohorte_periodo",
            "tenant_id",
            "cohorte_id",
            "periodo",
            postgresql_where="deleted_at IS NULL",
        ),
        Index("ix_liquidaciones_tenant_estado", "tenant_id", "estado"),
    )

    cohorte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    periodo: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="Formato AAAA-MM (ej: 2026-03)",
    )
    usuario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rol: Mapped[str] = mapped_column(String(50), nullable=False)
    monto_base: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    monto_plus: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    es_nexo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    excluido_por_factura: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Snapshot del flag facturador al momento del cierre (D4)",
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EstadoLiquidacion.ABIERTA,
    )
    cerrada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    cerrada_por_usuario_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
    )
    detalle_plus: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="JSON serializado con desglose de plus por grupo",
    )
