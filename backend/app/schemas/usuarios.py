"""Schemas Pydantic para gestión de usuarios con PII (C-07).

D-06: Enmascaramiento de PII en responses de listado:
- email: desencriptado y devuelto completo
- dni, cuil: últimos 4 caracteres (****XXXX)
- cbu, alias_cbu: NO devueltos en listado (solo en detalle)

Todos los schemas tienen extra='forbid' (regla dura).
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _mask_pii_last4(value: str | None) -> str | None:
    """Enmascara un campo PII mostrando solo los últimos 4 caracteres.

    Reemplaza todo excepto los últimos 4 caracteres con '****'.
    Si el valor es None, retorna None.
    Si el valor tiene menos de 4 caracteres, retorna '****'.
    """
    if value is None:
        return None
    stripped = value.strip()
    if len(stripped) <= 4:
        return "****"
    return f"****{stripped[-4:]}"


class UsuarioCreate(BaseModel):
    """Schema para crear un usuario. PII en texto plano (cifrado en repositorio)."""

    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., min_length=1, max_length=100)
    apellidos: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)
    estado: str = Field(..., min_length=1, max_length=20)
    legajo: str | None = Field(None, max_length=50)
    # PII opcionales — cifrados en repositorio
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo_profesional: str | None = None
    facturador: bool | None = None


class UsuarioUpdate(BaseModel):
    """Schema para actualización parcial de usuario. Todos los campos opcionales."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(None, min_length=1, max_length=100)
    apellidos: str | None = Field(None, min_length=1, max_length=100)
    email: str | None = Field(None, min_length=3, max_length=255)
    estado: str | None = Field(None, min_length=1, max_length=20)
    legajo: str | None = None
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo_profesional: str | None = None
    facturador: bool | None = None


class UsuarioListRead(BaseModel):
    """Schema para listado de usuarios — PII enmascarada (D-06).

    - email: devuelto completo (el ADMIN lo necesita para gestión)
    - dni, cuil: enmascarados (****XXXX — últimos 4)
    - cbu, alias_cbu: OMITIDOS en listado (solo en detalle)
    """

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
    # PII enmascarada
    dni: str | None = None
    cuil: str | None = None
    # NO incluye cbu ni alias_cbu — se omiten en listado (D-06)
    banco: str | None = None
    regional: str | None = None
    legajo_profesional: str | None = None
    facturador: bool | None = None

    @field_validator("dni", mode="before")
    @classmethod
    def _mask_dni(cls, v: Any) -> str | None:
        """Enmascara DNI a ****XXXX."""
        return _mask_pii_last4(str(v) if v is not None else None)

    @field_validator("cuil", mode="before")
    @classmethod
    def _mask_cuil(cls, v: Any) -> str | None:
        """Enmascara CUIL a ****XXXX."""
        return _mask_pii_last4(str(v) if v is not None else None)


class UsuarioDetailRead(BaseModel):
    """Schema para detalle individual — PII completa desencriptada (D-06).

    Disponible solo en GET /api/v1/admin/usuarios/{id}.
    """

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
    # PII completa — descifrada en repositorio antes de llegar aquí
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo_profesional: str | None = None
    facturador: bool | None = None


class PaginatedUsuariosResponse(BaseModel):
    """Response paginado de usuarios con PII enmascarada."""

    model_config = ConfigDict(extra="forbid")

    items: list[UsuarioListRead]
    total: int
    limit: int
    offset: int
