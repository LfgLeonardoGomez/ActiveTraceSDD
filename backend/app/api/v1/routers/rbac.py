"""Routers RBAC: roles, permisos, rol-permisos.

Protegidos por require_permission. Fail-closed: sin permiso → 403.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_active_user, get_db, require_permission
from app.schemas.rbac_schema import (
    PermissionContext,
    PermisoCreateSchema,
    PermisoResponseSchema,
    PermisoUpdateSchema,
    RolCreateSchema,
    RolPermisoCreateSchema,
    RolPermisoResponseSchema,
    RolResponseSchema,
    RolUpdateSchema,
)
from app.services.rbac_service import PermisoService, RolPermisoService, RolService

_common_responses = {
    403: {"description": "Permiso denegado"},
    404: {"description": "Recurso no encontrado"},
    422: {"description": "Validación fallida"},
}

router_roles = APIRouter(
    prefix="/api/v1/roles",
    tags=["roles"],
    responses={403: {"description": "Permiso denegado"}, 422: {"description": "Validación fallida"}},
)
router_permisos = APIRouter(
    prefix="/api/v1/permisos",
    tags=["permisos"],
    responses={403: {"description": "Permiso denegado"}, 422: {"description": "Validación fallida"}},
)
router_rol_permisos = APIRouter(
    prefix="/api/v1/rol-permisos",
    tags=["rol-permisos"],
    responses={403: {"description": "Permiso denegado"}, 422: {"description": "Validación fallida"}},
)


# ------------------------------------------------------------------
# Roles
# ------------------------------------------------------------------

@router_roles.get("", response_model=list[RolResponseSchema])
async def list_roles(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm_ctx: Annotated[PermissionContext, Depends(require_permission("roles:gestionar"))],
) -> list[RolResponseSchema]:
    """Lista roles activos del tenant. Requiere roles:gestionar."""
    service = RolService(db, current_user.tenant_id)
    roles = await service.list()
    return [
        RolResponseSchema(
            id=r.id,
            tenant_id=r.tenant_id,
            codigo=r.codigo,
            nombre=r.nombre,
            descripcion=r.descripcion,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in roles
    ]


@router_roles.post("", response_model=RolResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_role(
    body: RolCreateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm_ctx: Annotated[PermissionContext, Depends(require_permission("roles:gestionar"))],
) -> RolResponseSchema:
    """Crea un nuevo rol en el tenant."""
    service = RolService(db, current_user.tenant_id)
    rol = await service.create(**body.model_dump())
    return RolResponseSchema(
        id=rol.id,
        tenant_id=rol.tenant_id,
        codigo=rol.codigo,
        nombre=rol.nombre,
        descripcion=rol.descripcion,
        created_at=rol.created_at.isoformat() if rol.created_at else None,
    )


@router_roles.put("/{rol_id}", response_model=RolResponseSchema)
async def update_role(
    rol_id: UUID,
    body: RolUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm_ctx: Annotated[PermissionContext, Depends(require_permission("roles:gestionar"))],
) -> RolResponseSchema:
    """Actualiza un rol existente."""
    service = RolService(db, current_user.tenant_id)
    updated = await service.update(rol_id, body.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
    return RolResponseSchema(
        id=updated.id,
        tenant_id=updated.tenant_id,
        codigo=updated.codigo,
        nombre=updated.nombre,
        descripcion=updated.descripcion,
        created_at=updated.created_at.isoformat() if updated.created_at else None,
    )


@router_roles.delete("/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    rol_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm_ctx: Annotated[PermissionContext, Depends(require_permission("roles:gestionar"))],
) -> None:
    """Soft delete de un rol."""
    service = RolService(db, current_user.tenant_id)
    deleted = await service.delete(rol_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")


# ------------------------------------------------------------------
# Permisos
# ------------------------------------------------------------------

@router_permisos.get("", response_model=list[PermisoResponseSchema])
async def list_permisos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm_ctx: Annotated[PermissionContext, Depends(require_permission("permisos:gestionar"))],
) -> list[PermisoResponseSchema]:
    """Lista permisos activos del tenant."""
    service = PermisoService(db, current_user.tenant_id)
    perms = await service.list()
    return [
        PermisoResponseSchema(
            id=p.id,
            tenant_id=p.tenant_id,
            codigo=p.codigo,
            nombre=p.nombre,
            modulo=p.modulo,
            descripcion=p.descripcion,
            created_at=p.created_at.isoformat() if p.created_at else None,
        )
        for p in perms
    ]


@router_permisos.post("", response_model=PermisoResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_permiso(
    body: PermisoCreateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm_ctx: Annotated[PermissionContext, Depends(require_permission("permisos:gestionar"))],
) -> PermisoResponseSchema:
    """Crea un nuevo permiso en el tenant."""
    service = PermisoService(db, current_user.tenant_id)
    perm = await service.create(**body.model_dump())
    return PermisoResponseSchema(
        id=perm.id,
        tenant_id=perm.tenant_id,
        codigo=perm.codigo,
        nombre=perm.nombre,
        modulo=perm.modulo,
        descripcion=perm.descripcion,
        created_at=perm.created_at.isoformat() if perm.created_at else None,
    )


@router_permisos.put("/{permiso_id}", response_model=PermisoResponseSchema)
async def update_permiso(
    permiso_id: UUID,
    body: PermisoUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm_ctx: Annotated[PermissionContext, Depends(require_permission("permisos:gestionar"))],
) -> PermisoResponseSchema:
    """Actualiza un permiso existente."""
    service = PermisoService(db, current_user.tenant_id)
    updated = await service.update(permiso_id, body.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permiso no encontrado")
    return PermisoResponseSchema(
        id=updated.id,
        tenant_id=updated.tenant_id,
        codigo=updated.codigo,
        nombre=updated.nombre,
        modulo=updated.modulo,
        descripcion=updated.descripcion,
        created_at=updated.created_at.isoformat() if updated.created_at else None,
    )


@router_permisos.delete("/{permiso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permiso(
    permiso_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm_ctx: Annotated[PermissionContext, Depends(require_permission("permisos:gestionar"))],
) -> None:
    """Soft delete de un permiso."""
    service = PermisoService(db, current_user.tenant_id)
    deleted = await service.delete(permiso_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permiso no encontrado")


# ------------------------------------------------------------------
# Rol-Permisos
# ------------------------------------------------------------------

@router_roles.get("/{rol_id}/permisos", response_model=list[RolPermisoResponseSchema])
async def list_permiso_by_rol(
    rol_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm_ctx: Annotated[PermissionContext, Depends(require_permission("roles:gestionar"))],
) -> list[RolPermisoResponseSchema]:
    """Lista permisos asignados a un rol."""
    service = RolPermisoService(db, current_user.tenant_id)
    items = await service.list_by_rol(rol_id)
    return [
        RolPermisoResponseSchema(
            id=rp.id,
            tenant_id=rp.tenant_id,
            rol_id=rp.rol_id,
            permiso_id=rp.permiso_id,
            es_propio=rp.es_propio,
            created_at=rp.created_at.isoformat() if rp.created_at else None,
        )
        for rp in items
    ]


@router_rol_permisos.post("", response_model=RolPermisoResponseSchema, status_code=status.HTTP_201_CREATED)
async def assign_permiso(
    body: RolPermisoCreateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm_ctx: Annotated[PermissionContext, Depends(require_permission("roles:gestionar"))],
) -> RolPermisoResponseSchema:
    """Asigna un permiso a un rol."""
    service = RolPermisoService(db, current_user.tenant_id)
    rp = await service.assign(
        rol_id=body.rol_id,
        permiso_id=body.permiso_id,
        es_propio=body.es_propio,
    )
    return RolPermisoResponseSchema(
        id=rp.id,
        tenant_id=rp.tenant_id,
        rol_id=rp.rol_id,
        permiso_id=rp.permiso_id,
        es_propio=rp.es_propio,
        created_at=rp.created_at.isoformat() if rp.created_at else None,
    )


@router_rol_permisos.delete("/{rol_permiso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permiso(
    rol_permiso_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm_ctx: Annotated[PermissionContext, Depends(require_permission("roles:gestionar"))],
) -> None:
    """Quita una asignación rol-permiso (soft delete)."""
    service = RolPermisoService(db, current_user.tenant_id)
    removed = await service.remove(rol_permiso_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
