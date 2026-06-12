"""Schemas Pydantic v2 para SalarioBase (C-18)."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class SalarioBaseCreate(BaseModel):
    """Schema para crear un SalarioBase."""

    model_config = ConfigDict(extra="forbid")

    rol: str
    monto: Decimal
    desde: date
    hasta: date | None = None

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("monto debe ser mayor que cero")
        return v

    @field_validator("hasta")
    @classmethod
    def hasta_despues_de_desde(cls, v: date | None, info) -> date | None:
        if v is not None and "desde" in info.data and info.data["desde"] is not None:
            if v < info.data["desde"]:
                raise ValueError("hasta debe ser posterior o igual a desde")
        return v


class SalarioBaseUpdate(BaseModel):
    """Schema para actualizar parcialmente un SalarioBase."""

    model_config = ConfigDict(extra="forbid")

    monto: Decimal | None = None
    desde: date | None = None
    hasta: date | None = None

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("monto debe ser mayor que cero")
        return v


class SalarioBaseRead(BaseModel):
    """Schema de respuesta para SalarioBase."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    rol: str
    monto: Decimal
    desde: date
    hasta: date | None
