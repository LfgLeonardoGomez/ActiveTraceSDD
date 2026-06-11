"""Router de programas de materia (C-17).

Endpoints bajo /api/programas/:
  POST /       → crear programa (estructura:gestionar)
  GET  /       → listar programas (estructura:ver)
  GET  /{id}   → obtener programa (estructura:ver)
  PUT  /{id}   → actualizar programa (estructura:gestionar)
  DELETE /{id} → eliminar programa (estructura:gestionar)

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
from app.schemas.programa_materia import (
    ProgramaMateriaCreateSchema,
    ProgramaMateriaListResponseSchema,
    ProgramaMateriaResponseSchema,
    ProgramaMateriaUpdateSchema,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.programa_materia_service import ProgramaMateriaService

router = APIRouter(
    prefix="/api/programas",
    tags=["programas"],
    responses={
        403: {"description": "Permiso denegado"},
        404: {"description": "No encontrado"},
        409: {"description": "Conflicto (ya existe)"},
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


def _make_service(db: AsyncSession, current_user: CurrentUser) -> ProgramaMateriaService:
    return ProgramaMateriaService(
        db_session=db,
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# POST / — Crear programa
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=ProgramaMateriaResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un programa de materia",
)
async def crear_programa(
    body: ProgramaMateriaCreateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProgramaMateriaResponseSchema:
    service = _make_service(db, current_user)
    return await service.crear_programa(body.model_dump())


# ---------------------------------------------------------------------------
# GET / — Listar programas
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=ProgramaMateriaListResponseSchema,
    summary="Listar programas del tenant",
)
async def list_programas(
    materia_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ProgramaMateriaListResponseSchema:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    return await service.list_programas(
        materia_id=materia_id,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /{id} — Obtener programa
# ---------------------------------------------------------------------------

@router.get(
    "/{programa_id}",
    response_model=ProgramaMateriaResponseSchema,
    summary="Obtener un programa por ID",
)
async def get_programa(
    programa_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:ver"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProgramaMateriaResponseSchema:
    service = _make_service(db, current_user)
    return await service.get_programa(programa_id)


# ---------------------------------------------------------------------------
# PUT /{id} — Actualizar programa
# ---------------------------------------------------------------------------

@router.put(
    "/{programa_id}",
    response_model=ProgramaMateriaResponseSchema,
    summary="Actualizar campos editables de un programa",
)
async def update_programa(
    programa_id: UUID,
    body: ProgramaMateriaUpdateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProgramaMateriaResponseSchema:
    service = _make_service(db, current_user)
    return await service.update_programa(programa_id, body.model_dump())


# ---------------------------------------------------------------------------
# DELETE /{id} — Eliminar programa
# ---------------------------------------------------------------------------

@router.delete(
    "/{programa_id}",
    response_model=ProgramaMateriaResponseSchema,
    summary="Eliminar (soft delete) un programa",
)
async def delete_programa(
    programa_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProgramaMateriaResponseSchema:
    service = _make_service(db, current_user)
    return await service.delete_programa(programa_id)
