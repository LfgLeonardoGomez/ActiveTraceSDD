"""Schemas Pydantic v2 para el módulo de umbral de aprobación (C-10).

Todos los schemas tienen extra='forbid' (regla dura).
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

_DEFAULT_VALORES_APROBATORIOS = ["Satisfactorio", "Supera lo esperado"]


class UmbralMateriaRead(BaseModel):
    """Respuesta de lectura del umbral vigente para una asignación."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID | None = None
    tenant_id: UUID | None = None
    asignacion_id: UUID | None = None
    materia_id: UUID | None = None
    umbral_pct: int
    valores_aprobatorios: list[str]
    es_default: bool = Field(
        default=False,
        description="True si no existe configuración y se devuelve el valor por defecto",
    )


class UmbralMateriaUpsert(BaseModel):
    """Request para crear o actualizar el umbral de una materia."""

    model_config = ConfigDict(extra="forbid")

    umbral_pct: int = Field(
        default=60,
        ge=1,
        le=100,
        description="Porcentaje mínimo de nota numérica para aprobar (RN-03)",
    )
    valores_aprobatorios: list[str] = Field(
        default_factory=lambda: list(_DEFAULT_VALORES_APROBATORIOS),
        min_length=1,
        description="Valores textuales que cuentan como aprobado (RN-02)",
    )
