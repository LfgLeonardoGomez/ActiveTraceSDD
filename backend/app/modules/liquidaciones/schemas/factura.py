"""Schemas Pydantic v2 para Factura (C-18)."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FacturaCreate(BaseModel):
    """Schema para crear una Factura."""

    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    periodo: str
    detalle: str | None = None
    referencia_archivo: str
    tamano_kb: Decimal | None = None


class FacturaRead(BaseModel):
    """Schema de respuesta para Factura."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    usuario_id: UUID
    periodo: str
    detalle: str | None
    referencia_archivo: str
    tamano_kb: Decimal | None
    estado: str
    cargada_at: datetime
    abonada_at: datetime | None


class FacturaListFilter(BaseModel):
    """Filtros para el listado de facturas."""

    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID | None = None
    estado: str | None = None
    desde: str | None = None
    """Período inicio (AAAA-MM)."""
    hasta: str | None = None
    """Período fin (AAAA-MM)."""
    q: str | None = None
    """Búsqueda libre en campo detalle (case-insensitive)."""
    page: int = 1
    page_size: int = 20
