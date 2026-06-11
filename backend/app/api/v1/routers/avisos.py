"""Router de avisos y acknowledgment (C-15).

Endpoints bajo /api/avisos/:
  POST /              → crear aviso (publicar)
  GET  /              → listar avisos (publicar)
  GET  /{id}          → obtener aviso (publicar)
  PATCH /{id}         → actualizar aviso (publicar)
  DELETE /{id}        → eliminar aviso (publicar)
  GET  /mis-avisos    → listar avisos visibles para el usuario (confirmar)
  POST /{id}/confirmar → confirmar lectura de aviso (confirmar)

Guards: require_permission por endpoint. Identidad EXCLUSIVAMENTE del JWT.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    get_current_active_user,
    get_db,
    require_permission,
)
from app.schemas.aviso import (
    AvisoCreateSchema,
    AvisoListResponseSchema,
    AvisoParaUsuarioListSchema,
    AvisoResponseSchema,
    AvisoUpdateSchema,
    AcknowledgmentResponseSchema,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.aviso_service import AvisoService

router = APIRouter(
    prefix="/api/avisos",
    tags=["avisos"],
    responses={
        403: {"description": "Permiso denegado"},
        404: {"description": "No encontrado"},
        409: {"description": "Conflicto (ya confirmado)"},
    },
)

_MAX_PAGE_SIZE = 100
_DEFAULT_PAGE_SIZE = 50


def _validate_page_size(page_size: int) -> int:
    if page_size > _MAX_PAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"page_size no puede superar {_MAX_PAGE_SIZE}",
        )
    if page_size < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="page_size debe ser al menos 1",
        )
    return page_size


def _make_service(db: AsyncSession, current_user: CurrentUser) -> AvisoService:
    return AvisoService(
        db_session=db,
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# POST / — Crear aviso
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=AvisoResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un aviso",
)
async def crear_aviso(
    body: AvisoCreateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("avisos:publicar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvisoResponseSchema:
    service = _make_service(db, current_user)
    return await service.crear_aviso(body.model_dump())


# ---------------------------------------------------------------------------
# GET / — Listar avisos (gestión)
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=AvisoListResponseSchema,
    summary="Listar avisos del tenant",
)
async def list_avisos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    alcance: str | None = Query(default=None),
    activo: bool | None = Query(default=None),
    severidad: str | None = Query(default=None),
    _perm: Annotated[PermissionContext, Depends(require_permission("avisos:publicar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AvisoListResponseSchema:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    return await service.list_avisos(
        page=page,
        page_size=page_size,
        alcance=alcance,
        activo=activo,
        severidad=severidad,
    )


# ---------------------------------------------------------------------------
# GET /{id} — Obtener aviso
# ---------------------------------------------------------------------------

@router.get(
    "/{aviso_id}",
    response_model=AvisoResponseSchema,
    summary="Obtener un aviso por ID",
)
async def get_aviso(
    aviso_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("avisos:publicar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvisoResponseSchema:
    service = _make_service(db, current_user)
    return await service.get_aviso(aviso_id)


# ---------------------------------------------------------------------------
# PATCH /{id} — Actualizar aviso
# ---------------------------------------------------------------------------

@router.patch(
    "/{aviso_id}",
    response_model=AvisoResponseSchema,
    summary="Actualizar campos editables de un aviso",
)
async def update_aviso(
    aviso_id: UUID,
    body: AvisoUpdateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("avisos:publicar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvisoResponseSchema:
    service = _make_service(db, current_user)
    return await service.update_aviso(aviso_id, body.model_dump())


# ---------------------------------------------------------------------------
# DELETE /{id} — Eliminar aviso
# ---------------------------------------------------------------------------

@router.delete(
    "/{aviso_id}",
    response_model=AvisoResponseSchema,
    summary="Eliminar (soft delete) un aviso",
)
async def delete_aviso(
    aviso_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("avisos:publicar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvisoResponseSchema:
    service = _make_service(db, current_user)
    return await service.delete_aviso(aviso_id)


# ---------------------------------------------------------------------------
# GET /mis-avisos — Avisos visibles para el usuario
# ---------------------------------------------------------------------------

@router.get(
    "/mis-avisos",
    response_model=AvisoParaUsuarioListSchema,
    summary="Listar avisos visibles para el usuario actual",
)
async def list_mis_avisos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    _perm: Annotated[PermissionContext, Depends(require_permission("avisos:confirmar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AvisoParaUsuarioListSchema:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    return await service.list_mis_avisos(page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# POST /{id}/confirmar — Confirmar aviso
# ---------------------------------------------------------------------------

@router.post(
    "/{aviso_id}/confirmar",
    response_model=AcknowledgmentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Confirmar lectura de un aviso",
)
async def confirmar_aviso(
    aviso_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("avisos:confirmar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AcknowledgmentResponseSchema:
    service = _make_service(db, current_user)
    return await service.confirmar_aviso(aviso_id)
