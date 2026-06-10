"""Router de gestión de usuarios (C-07).

Todos los endpoints protegidos por require_permission("usuarios:gestionar").
Identidad y tenant_id provienen EXCLUSIVAMENTE del JWT verificado.
Fail-closed: sin permiso → 403 (sin excepciones).

Endpoints:
- POST   /api/v1/admin/usuarios          → crear usuario (201)
- GET    /api/v1/admin/usuarios          → listar usuarios paginados
- GET    /api/v1/admin/usuarios/{id}     → detalle con PII completa
- PUT    /api/v1/admin/usuarios/{id}     → actualizar (parcial)
- DELETE /api/v1/admin/usuarios/{id}     → soft delete (204)
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    get_current_active_user,
    get_db,
    require_permission,
)
from app.schemas.rbac_schema import PermissionContext
from app.schemas.usuarios import (
    PaginatedUsuariosResponse,
    UsuarioCreate,
    UsuarioDetailRead,
    UsuarioListRead,
    UsuarioUpdate,
)
from app.services.usuarios import UsuarioService

_common_responses = {
    403: {"description": "Permiso denegado"},
    404: {"description": "Usuario no encontrado"},
    409: {"description": "Conflicto de unicidad (email duplicado en tenant)"},
    422: {"description": "Validación fallida"},
}

router = APIRouter(
    prefix="/api/v1/admin/usuarios",
    tags=["usuarios"],
    responses=_common_responses,
)


@router.post(
    "",
    response_model=UsuarioDetailRead,
    status_code=status.HTTP_201_CREATED,
)
async def crear_usuario(
    body: UsuarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("usuarios:gestionar"))],
) -> UsuarioDetailRead:
    """Crea un usuario en el tenant del actor autenticado."""
    service = UsuarioService(db, current_user.tenant_id)
    usuario = await service.crear_usuario(
        nombre=body.nombre,
        apellidos=body.apellidos,
        email=body.email,
        estado=body.estado,
        legajo=body.legajo,
        dni=body.dni,
        cuil=body.cuil,
        cbu=body.cbu,
        alias_cbu=body.alias_cbu,
        banco=body.banco,
        regional=body.regional,
        legajo_profesional=body.legajo_profesional,
        facturador=body.facturador,
    )
    return UsuarioDetailRead.model_validate(usuario)


@router.get(
    "",
    response_model=PaginatedUsuariosResponse,
)
async def listar_usuarios(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("usuarios:gestionar"))],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    estado: Annotated[str | None, Query()] = None,
) -> PaginatedUsuariosResponse:
    """Lista usuarios del tenant con paginación y PII enmascarada."""
    service = UsuarioService(db, current_user.tenant_id)
    items, total = await service.listar_usuarios(limit=limit, offset=offset, estado=estado)
    return PaginatedUsuariosResponse(
        items=[UsuarioListRead.model_validate(u) for u in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{usuario_id}",
    response_model=UsuarioDetailRead,
)
async def obtener_usuario(
    usuario_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("usuarios:gestionar"))],
) -> UsuarioDetailRead:
    """Obtiene detalle de un usuario por ID con PII completa."""
    service = UsuarioService(db, current_user.tenant_id)
    usuario = await service.obtener_usuario(usuario_id)
    return UsuarioDetailRead.model_validate(usuario)


@router.put(
    "/{usuario_id}",
    response_model=UsuarioDetailRead,
)
async def actualizar_usuario(
    usuario_id: UUID,
    body: UsuarioUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("usuarios:gestionar"))],
) -> UsuarioDetailRead:
    """Actualiza campos de un usuario (parcial — solo los campos enviados)."""
    service = UsuarioService(db, current_user.tenant_id)
    data = body.model_dump(exclude_unset=True)
    usuario = await service.actualizar_usuario(usuario_id, data)
    return UsuarioDetailRead.model_validate(usuario)


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def eliminar_usuario(
    usuario_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("usuarios:gestionar"))],
) -> None:
    """Soft delete de usuario (setea deleted_at)."""
    service = UsuarioService(db, current_user.tenant_id)
    await service.eliminar_usuario(usuario_id)
