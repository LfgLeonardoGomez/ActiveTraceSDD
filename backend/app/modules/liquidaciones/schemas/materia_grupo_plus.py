"""Schemas Pydantic v2 para MateriaGrupoPlus (C-18)."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class MateriaGrupoPlusCreate(BaseModel):
    """Schema para crear un MateriaGrupoPlus."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    grupo: str
    desde: date
    hasta: date | None = None

    @field_validator("hasta")
    @classmethod
    def hasta_despues_de_desde(cls, v: date | None, info) -> date | None:
        if v is not None and "desde" in info.data and info.data["desde"] is not None:
            if v < info.data["desde"]:
                raise ValueError("hasta debe ser posterior o igual a desde")
        return v


class MateriaGrupoPlusUpdate(BaseModel):
    """Schema para actualizar parcialmente un MateriaGrupoPlus."""

    model_config = ConfigDict(extra="forbid")

    grupo: str | None = None
    desde: date | None = None
    hasta: date | None = None


class MateriaGrupoPlusRead(BaseModel):
    """Schema de respuesta para MateriaGrupoPlus."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    grupo: str
    desde: date
    hasta: date | None
