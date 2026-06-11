"""Router de tareas y comentarios (C-16).

Endpoints bajo /api/tareas/:
  POST /              → crear tarea
  GET  /              → listar tareas (admin)
  GET  /{id}          → obtener tarea
  PATCH /{id}         → actualizar tarea
  DELETE /{id}        → eliminar tarea
  GET  /mis-tareas    → listar tareas asignadas al usuario
  PATCH /{id}/estado  → cambiar estado
  POST /{id}/aprobar  → aprobar tarea resuelta
  POST /{id}/devolver → devolver tarea resuelta
  POST /{id}/delegar  → delegar tarea
  POST /{id}/comentarios → crear comentario
  GET  /{id}/comentarios → listar comentarios

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
from app.schemas.tarea import (
    ComentarioCreateSchema,
    ComentarioListResponseSchema,
    ComentarioResponseSchema,
    DelegarTareaSchema,
    DevolverTareaSchema,
    TareaCreateSchema,
    TareaEstadoSchema,
    TareaListResponseSchema,
    TareaResponseSchema,
    TareaUpdateSchema,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.tarea_service import TareaService

router = APIRouter(
    prefix="/api/tareas",
    tags=["tareas"],
    responses={
        403: {"description": "Permiso denegado"},
        404: {"description": "No encontrado"},
        422: {"description": "Transición inválida"},
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


def _make_service(db: AsyncSession, current_user: CurrentUser) -> TareaService:
    return TareaService(
        db_session=db,
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# POST / — Crear tarea
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=TareaResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una tarea",
)
async def crear_tarea(
    body: TareaCreateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaResponseSchema:
    service = _make_service(db, current_user)
    data = body.model_dump()
    data["asignado_por"] = current_user.id
    return await service.crear(data)


# ---------------------------------------------------------------------------
# GET / — Listar tareas (admin)
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=TareaListResponseSchema,
    summary="Listar tareas del tenant",
)
async def list_tareas(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    estado: str | None = Query(default=None),
    asignado_a: UUID | None = Query(default=None),
    materia_id: UUID | None = Query(default=None),
    q: str | None = Query(default=None),
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> TareaListResponseSchema:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    filtros = {
        "estado": estado,
        "asignado_a": asignado_a,
        "materia_id": materia_id,
        "search": q,
    }
    return await service.list_admin(filtros, page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# GET /mis-tareas — Mis tareas
# ---------------------------------------------------------------------------

@router.get(
    "/mis-tareas",
    response_model=TareaListResponseSchema,
    summary="Listar tareas asignadas al usuario actual",
)
async def list_mis_tareas(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    estado: str | None = Query(default=None),
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> TareaListResponseSchema:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    return await service.list_mis_tareas(page=page, page_size=page_size, estado=estado)


# ---------------------------------------------------------------------------
# GET /{id} — Obtener tarea
# ---------------------------------------------------------------------------

@router.get(
    "/{tarea_id}",
    response_model=TareaResponseSchema,
    summary="Obtener una tarea por ID",
)
async def get_tarea(
    tarea_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaResponseSchema:
    service = _make_service(db, current_user)
    return await service.get_tarea(tarea_id)


# ---------------------------------------------------------------------------
# PATCH /{id} — Actualizar tarea
# ---------------------------------------------------------------------------

@router.patch(
    "/{tarea_id}",
    response_model=TareaResponseSchema,
    summary="Actualizar campos editables de una tarea",
)
async def update_tarea(
    tarea_id: UUID,
    body: TareaUpdateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaResponseSchema:
    service = _make_service(db, current_user)
    return await service.update_tarea(tarea_id, body.model_dump())


# ---------------------------------------------------------------------------
# DELETE /{id} — Eliminar tarea
# ---------------------------------------------------------------------------

@router.delete(
    "/{tarea_id}",
    response_model=TareaResponseSchema,
    summary="Eliminar (soft delete) una tarea",
)
async def delete_tarea(
    tarea_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaResponseSchema:
    service = _make_service(db, current_user)
    return await service.delete_tarea(tarea_id)


# ---------------------------------------------------------------------------
# PATCH /{id}/estado — Cambiar estado
# ---------------------------------------------------------------------------

@router.patch(
    "/{tarea_id}/estado",
    response_model=TareaResponseSchema,
    summary="Cambiar estado de una tarea",
)
async def cambiar_estado(
    tarea_id: UUID,
    body: TareaEstadoSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaResponseSchema:
    service = _make_service(db, current_user)
    return await service.cambiar_estado(tarea_id, body.estado.value, current_user.id)


# ---------------------------------------------------------------------------
# POST /{id}/aprobar — Aprobar tarea
# ---------------------------------------------------------------------------

@router.post(
    "/{tarea_id}/aprobar",
    response_model=TareaResponseSchema,
    summary="Aprobar una tarea resuelta",
)
async def aprobar_tarea(
    tarea_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaResponseSchema:
    service = _make_service(db, current_user)
    return await service.aprobar(tarea_id)


# ---------------------------------------------------------------------------
# POST /{id}/devolver — Devolver tarea
# ---------------------------------------------------------------------------

@router.post(
    "/{tarea_id}/devolver",
    response_model=TareaResponseSchema,
    summary="Devolver una tarea resuelta al docente",
)
async def devolver_tarea(
    tarea_id: UUID,
    body: DevolverTareaSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaResponseSchema:
    service = _make_service(db, current_user)
    return await service.devolver(tarea_id, body.observacion)


# ---------------------------------------------------------------------------
# POST /{id}/delegar — Delegar tarea
# ---------------------------------------------------------------------------

@router.post(
    "/{tarea_id}/delegar",
    response_model=TareaResponseSchema,
    summary="Delegar una tarea a otro docente",
)
async def delegar_tarea(
    tarea_id: UUID,
    body: DelegarTareaSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaResponseSchema:
    service = _make_service(db, current_user)
    return await service.delegar(tarea_id, body.nuevo_asignado_id)


# ---------------------------------------------------------------------------
# POST /{id}/comentarios — Crear comentario
# ---------------------------------------------------------------------------

@router.post(
    "/{tarea_id}/comentarios",
    response_model=ComentarioResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar un comentario a una tarea",
)
async def crear_comentario(
    tarea_id: UUID,
    body: ComentarioCreateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComentarioResponseSchema:
    service = _make_service(db, current_user)
    return await service.crear_comentario(tarea_id, body.model_dump())


# ---------------------------------------------------------------------------
# GET /{id}/comentarios — Listar comentarios
# ---------------------------------------------------------------------------

@router.get(
    "/{tarea_id}/comentarios",
    response_model=ComentarioListResponseSchema,
    summary="Listar comentarios de una tarea",
)
async def list_comentarios(
    tarea_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    _perm: Annotated[PermissionContext, Depends(require_permission("tareas:gestionar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ComentarioListResponseSchema:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    return await service.list_comentarios(tarea_id, page=page, page_size=page_size)
