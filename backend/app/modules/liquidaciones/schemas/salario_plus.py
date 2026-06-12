"""Schemas Pydantic v2 para SalarioPlus (C-18)."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class SalarioPlusCreate(BaseModel):
    """Schema para crear un SalarioPlus."""

    model_config = ConfigDict(extra="forbid")

    grupo: str
    rol: str
    descripcion: str | None = None
    monto: Decimal
    tope_acumulacion: Decimal | None = None
    desde: date
    hasta: date | None = None

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("monto debe ser mayor que cero")
        return v

    @field_validator("tope_acumulacion")
    @classmethod
    def tope_positivo(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("tope_acumulacion debe ser mayor que cero o null (sin tope)")
        return v

    @field_validator("hasta")
    @classmethod
    def hasta_despues_de_desde(cls, v: date | None, info) -> date | None:
        if v is not None and "desde" in info.data and info.data["desde"] is not None:
            if v < info.data["desde"]:
                raise ValueError("hasta debe ser posterior o igual a desde")
        return v


class SalarioPlusUpdate(BaseModel):
    """Schema para actualizar parcialmente un SalarioPlus."""

    model_config = ConfigDict(extra="forbid")

    descripcion: str | None = None
    monto: Decimal | None = None
    tope_acumulacion: Decimal | None = None
    desde: date | None = None
    hasta: date | None = None

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("monto debe ser mayor que cero")
        return v

    @field_validator("tope_acumulacion")
    @classmethod
    def tope_positivo(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("tope_acumulacion debe ser mayor que cero o null (sin tope)")
        return v


class SalarioPlusRead(BaseModel):
    """Schema de respuesta para SalarioPlus."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    grupo: str
    rol: str
    descripcion: str | None
    monto: Decimal
    tope_acumulacion: Decimal | None
    desde: date
    hasta: date | None
