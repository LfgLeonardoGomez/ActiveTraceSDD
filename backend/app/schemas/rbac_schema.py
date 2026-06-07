"""Schemas Pydantic para RBAC.

Todos usan extra='forbid' como regla dura del proyecto.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RolCreateSchema(BaseModel):
    """Solicitud de creación de rol."""

    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str
    descripcion: str | None = None


class RolUpdateSchema(BaseModel):
    """Solicitud de actualización de rol (parcial)."""

    model_config = ConfigDict(extra="forbid")

    codigo: str | None = None
    nombre: str | None = None
    descripcion: str | None = None


class RolResponseSchema(BaseModel):
    """Respuesta de rol."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    codigo: str
    nombre: str
    descripcion: str | None = None
    created_at: str | None = None


class PermisoCreateSchema(BaseModel):
    """Solicitud de creación de permiso."""

    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str
    modulo: str
    descripcion: str | None = None


class PermisoUpdateSchema(BaseModel):
    """Solicitud de actualización de permiso (parcial)."""

    model_config = ConfigDict(extra="forbid")

    codigo: str | None = None
    nombre: str | None = None
    modulo: str | None = None
    descripcion: str | None = None


class PermisoResponseSchema(BaseModel):
    """Respuesta de permiso."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    codigo: str
    nombre: str
    modulo: str
    descripcion: str | None = None
    created_at: str | None = None


class RolPermisoCreateSchema(BaseModel):
    """Solicitud de asignación rol-permiso."""

    model_config = ConfigDict(extra="forbid")

    rol_id: UUID
    permiso_id: UUID
    es_propio: bool = False


class RolPermisoResponseSchema(BaseModel):
    """Respuesta de asignación rol-permiso."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    rol_id: UUID
    permiso_id: UUID
    es_propio: bool
    created_at: str | None = None


class PermissionContext(BaseModel):
    """Contexto de permiso devuelto por require_permission.

    Incluye el conjunto de permisos efectivos para que el service
    downstream pueda consultarlo si necesita aplicar filtros propio.
    """

    model_config = ConfigDict(extra="forbid")

    has_permission: bool
    is_propio: bool
    effective_permissions: set[str] = set()
