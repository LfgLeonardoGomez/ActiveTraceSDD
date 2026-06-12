"""Schemas Pydantic para edición de perfil de usuario (C-20).

Reglas duras:
- extra='forbid' en todo schema.
- PerfilUpdate NO incluye cuil (read-only en schema level).
- PerfilRead devuelve los campos del usuario con PII descifrada.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PerfilUpdate(BaseModel):
    """Schema para actualización parcial de perfil propio."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    apellidos: str | None = None
    email: str | None = None
    dni: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo_profesional: str | None = None
    facturador: bool | None = None


class PerfilRead(BaseModel):
    """Schema para lectura de perfil propio (PII completa)."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: UUID
    tenant_id: UUID
    nombre: str
    apellidos: str
    email: str
    estado: str
    legajo: str | None = None
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo_profesional: str | None = None
    facturador: bool | None = None
