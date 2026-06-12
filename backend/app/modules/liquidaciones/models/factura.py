"""Modelo ORM Factura (C-18).

Comprobante presentado por docentes facturantes (Usuario.facturador=True).
El archivo se referencia de forma opaca vía referencia_archivo (D6).
Solo dos estados: Pendiente → Abonada (RN-39).
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin
from app.modules.liquidaciones.models.enums import EstadoFactura


class Factura(BaseModelMixin, Base):
    """Factura de docente facturante con referencia opaca al archivo.

    estado: Pendiente → Abonada (RN-39). Sin estado Cancelada.
    Soft delete como mecanismo de cancelación (append-only audit).
    """

    __tablename__ = "facturas"
    __table_args__ = (
        Index("ix_facturas_tenant_usuario_periodo", "tenant_id", "usuario_id", "periodo"),
        Index("ix_facturas_tenant_estado", "tenant_id", "estado"),
    )

    usuario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    periodo: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="Formato AAAA-MM (ej: 2026-03)",
    )
    detalle: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None,
        comment="Texto libre de descripción del servicio facturado"
    )
    referencia_archivo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Puntero opaco al archivo en el storage (D6). NO guarda binario en DB.",
    )
    tamano_kb: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, default=None,
        comment="Tamaño del archivo en kilobytes"
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EstadoFactura.PENDIENTE,
    )
    cargada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    abonada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
