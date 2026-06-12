"""Schemas Pydantic v2 para Liquidacion (C-18)."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class PlusDetalleItem(BaseModel):
    """Detalle de un plus acumulado para una fila de liquidación."""

    model_config = ConfigDict(extra="forbid")

    grupo: str
    monto_unitario: Decimal
    n_comisiones_detectadas: int
    n_comisiones_acumuladas: int
    tope_acumulacion: Decimal | None
    subtotal: Decimal


class LiquidacionWarning(BaseModel):
    """Warning estructurado para gaps de grilla salarial."""

    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    rol: str
    motivo: str
    """Ej: 'SIN_BASE_VIGENTE'"""


class LiquidacionFilaRead(BaseModel):
    """Fila de liquidación en la respuesta del cálculo/vista."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID | None = None
    usuario_id: UUID
    rol: str
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool
    estado: str
    cerrada_at: datetime | None = None
    cerrada_por_usuario_id: UUID | None = None
    plus_detalle: list[PlusDetalleItem] = []


class LiquidacionPeriodoResponse(BaseModel):
    """Respuesta completa del cálculo/vista de un período.

    Tres segmentos (RN-36/RN-38):
    - general: PROFESOR/TUTOR/COORDINADOR no facturantes.
    - nexo: rol NEXO no facturante (suma al total_sin_factura).
    - facturantes: docentes facturantes (informativo, excluido del total).
    """

    model_config = ConfigDict(extra="forbid")

    cohorte_id: UUID
    periodo: str
    estado: str
    """'Abierta' (calculado on-demand) o 'Cerrada' (snapshot persistido)."""
    cerrada_at: datetime | None = None
    cerrada_por_usuario_id: UUID | None = None

    segmentos: "SegmentosLiquidacion"
    total_sin_factura: Decimal
    """Suma de general + nexo."""
    total_con_factura: Decimal
    """Suma de facturantes (informativo)."""
    warnings: list[LiquidacionWarning] = []


class SegmentosLiquidacion(BaseModel):
    """Los tres segmentos contables de la vista de liquidación."""

    model_config = ConfigDict(extra="forbid")

    general: list[LiquidacionFilaRead] = []
    nexo: list[LiquidacionFilaRead] = []
    facturantes: list[LiquidacionFilaRead] = []


# Rebuild para referencia forward
LiquidacionPeriodoResponse.model_rebuild()


class CerrarLiquidacionRequest(BaseModel):
    """Body del endpoint POST /liquidaciones/{cohorte_id}/{periodo}/cerrar.

    Defensa anti-TOCTOU: el campo `periodo` del body debe coincidir con
    el de la URL. Si no coinciden → 400 Bad Request.
    """

    model_config = ConfigDict(extra="forbid")

    confirmar_cierre: bool
    periodo: str
    """Debe coincidir con el período de la URL."""

    @field_validator("confirmar_cierre")
    @classmethod
    def debe_ser_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("confirmar_cierre debe ser true para proceder con el cierre")
        return v


class HistorialPeriodoItem(BaseModel):
    """Item del historial de liquidaciones cerradas."""

    model_config = ConfigDict(extra="forbid")

    cohorte_id: UUID
    periodo: str
    total_filas: int
    total_sin_factura: Decimal
    total_con_factura: Decimal
    cerrada_at: datetime
    cerrada_por_usuario_id: UUID


class HistorialResponse(BaseModel):
    """Respuesta paginada del historial de liquidaciones cerradas."""

    model_config = ConfigDict(extra="forbid")

    items: list[HistorialPeriodoItem]
    total: int
    page: int
    page_size: int
