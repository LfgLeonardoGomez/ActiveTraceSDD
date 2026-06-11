"""Router de fechas académicas (C-17).

Endpoints bajo /api/fechas-academicas/:
  POST /       → crear fecha (estructura:gestionar)
  GET  /       → listar fechas (estructura:ver)
  GET  /{id}   → obtener fecha (estructura:ver)
  PUT  /{id}   → actualizar fecha (estructura:gestionar)
  DELETE /{id} → eliminar fecha (estructura:gestionar)
  GET  /{materia_id}/{cohorte_id}/lms-content → generar contenido LMS (estructura:ver)

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
    FechaAcademicaCreateSchema,
    FechaAcademicaListResponseSchema,
    FechaAcademicaResponseSchema,
    FechaAcademicaUpdateSchema,
    LMSContentResponseSchema,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.programa_materia_service import FechaAcademicaService, GeneracionLMSService

router = APIRouter(
    prefix="/api/fechas-academicas",
    tags=["fechas-academicas"],
    responses={
        403: {"description": "Permiso denegado"},
        404: {"description": "No encontrado"},
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


def _make_service(db: AsyncSession, current_user: CurrentUser) -> FechaAcademicaService:
    return FechaAcademicaService(
        db_session=db,
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# POST / — Crear fecha
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=FechaAcademicaResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una fecha académica",
)
async def crear_fecha(
    body: FechaAcademicaCreateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FechaAcademicaResponseSchema:
    service = _make_service(db, current_user)
    return await service.crear_fecha(body.model_dump())


# ---------------------------------------------------------------------------
# GET / — Listar fechas
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=FechaAcademicaListResponseSchema,
    summary="Listar fechas académicas del tenant",
)
async def list_fechas(
    materia_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    cohorte_id: UUID | None = None,
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> FechaAcademicaListResponseSchema:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    if cohorte_id is not None:
        return await service.list_fechas_por_cohorte(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            page=page,
            page_size=page_size,
        )
    return await service.list_fechas(
        materia_id=materia_id,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /{id} — Obtener fecha
# ---------------------------------------------------------------------------

@router.get(
    "/{fecha_id}",
    response_model=FechaAcademicaResponseSchema,
    summary="Obtener una fecha académica por ID",
)
async def get_fecha(
    fecha_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:ver"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FechaAcademicaResponseSchema:
    service = _make_service(db, current_user)
    return await service.get_fecha(fecha_id)


# ---------------------------------------------------------------------------
# PUT /{id} — Actualizar fecha
# ---------------------------------------------------------------------------

@router.put(
    "/{fecha_id}",
    response_model=FechaAcademicaResponseSchema,
    summary="Actualizar campos editables de una fecha académica",
)
async def update_fecha(
    fecha_id: UUID,
    body: FechaAcademicaUpdateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FechaAcademicaResponseSchema:
    service = _make_service(db, current_user)
    return await service.update_fecha(fecha_id, body.model_dump())


# ---------------------------------------------------------------------------
# DELETE /{id} — Eliminar fecha
# ---------------------------------------------------------------------------

@router.delete(
    "/{fecha_id}",
    response_model=FechaAcademicaResponseSchema,
    summary="Eliminar (soft delete) una fecha académica",
)
async def delete_fecha(
    fecha_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FechaAcademicaResponseSchema:
    service = _make_service(db, current_user)
    return await service.delete_fecha(fecha_id)


# ---------------------------------------------------------------------------
# GET /{materia_id}/{cohorte_id}/lms-content — Generar contenido LMS
# ---------------------------------------------------------------------------

@router.get(
    "/{materia_id}/{cohorte_id}/lms-content",
    response_model=LMSContentResponseSchema,
    summary="Generar fragmento HTML para el aula virtual",
)
async def generar_lms_content(
    materia_id: UUID,
    cohorte_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:ver"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LMSContentResponseSchema:
    service = GeneracionLMSService(
        db_session=db,
        tenant_id=current_user.tenant_id,
    )
    return await service.generar_contenido_lms(materia_id, cohorte_id)
