"""Router de comunicaciones salientes (C-12).

Endpoints bajo /api/comunicaciones/:
  6.2  POST /preview                    → preview sin persistencia
  6.3  POST /lote                       → encolar lote de mensajes
  6.4  GET  /lote/{lote_id}/estado      → estado agregado del lote
  6.5  POST /lote/{lote_id}/aprobar     → aprobar lote completo
  6.6  POST /lote/{lote_id}/cancelar    → cancelar lote completo
  6.7  POST /{comunicacion_id}/cancelar → cancelar mensaje individual
  6.8  POST /{comunicacion_id}/retry    → reintentar mensaje con Error

Guard: require_permission("comunicacion:enviar") o "comunicacion:aprobar" según endpoint.
Identidad y tenant_id EXCLUSIVAMENTE del JWT verificado.
Nota de seguridad: destinatario NUNCA aparece en logs ni respuestas.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    get_current_active_user,
    get_db,
    require_permission,
)
from app.schemas.comunicacion import (
    ComunicacionLoteRequestSchema,
    ComunicacionLoteResponseSchema,
    ComunicacionPreviewItemSchema,
    ComunicacionPreviewRequestSchema,
    LoteEstadoSchema,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.comunicacion_service import ComunicacionService

router = APIRouter(
    prefix="/api/comunicaciones",
    tags=["comunicaciones"],
    responses={
        403: {"description": "Permiso denegado"},
        404: {"description": "No encontrado"},
        422: {"description": "Validación fallida o transición inválida"},
    },
)


def _make_service(db: AsyncSession, current_user: CurrentUser) -> ComunicacionService:
    """Instancia el service con contexto del JWT."""
    return ComunicacionService(
        db_session=db,
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# 6.2 POST /preview
# ---------------------------------------------------------------------------


@router.post(
    "/preview",
    response_model=list[ComunicacionPreviewItemSchema],
    summary="Preview de mensaje con variables resueltas (sin persistencia)",
)
async def preview_comunicacion(
    body: ComunicacionPreviewRequestSchema,
    perm: Annotated[PermissionContext, Depends(require_permission("comunicacion:enviar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[ComunicacionPreviewItemSchema]:
    service = _make_service(db, current_user)
    return await service.preview(body, perm)


# ---------------------------------------------------------------------------
# 6.3 POST /lote
# ---------------------------------------------------------------------------


@router.post(
    "/lote",
    response_model=ComunicacionLoteResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Encolar lote de comunicaciones",
)
async def encolar_lote(
    body: ComunicacionLoteRequestSchema,
    perm: Annotated[PermissionContext, Depends(require_permission("comunicacion:enviar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ComunicacionLoteResponseSchema:
    service = _make_service(db, current_user)
    return await service.encolar_lote(body, perm)


# ---------------------------------------------------------------------------
# 6.4 GET /lote/{lote_id}/estado
# ---------------------------------------------------------------------------


@router.get(
    "/lote/{lote_id}/estado",
    response_model=LoteEstadoSchema,
    summary="Estado agregado del lote de comunicaciones",
)
async def get_estado_lote(
    lote_id: UUID,
    perm: Annotated[PermissionContext, Depends(require_permission("comunicacion:enviar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> LoteEstadoSchema:
    service = _make_service(db, current_user)
    return await service.get_estado_lote(lote_id, perm)


# ---------------------------------------------------------------------------
# 6.5 POST /lote/{lote_id}/aprobar
# ---------------------------------------------------------------------------


@router.post(
    "/lote/{lote_id}/aprobar",
    summary="Aprobar lote completo para despacho",
)
async def aprobar_lote(
    lote_id: UUID,
    perm: Annotated[PermissionContext, Depends(require_permission("comunicacion:aprobar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    service = _make_service(db, current_user)
    filas = await service.aprobar_lote(lote_id, perm)
    return {"aprobados": filas}


# ---------------------------------------------------------------------------
# 6.6 POST /lote/{lote_id}/cancelar
# ---------------------------------------------------------------------------


@router.post(
    "/lote/{lote_id}/cancelar",
    summary="Cancelar todos los mensajes Pendiente del lote",
)
async def cancelar_lote(
    lote_id: UUID,
    perm: Annotated[PermissionContext, Depends(require_permission("comunicacion:aprobar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    service = _make_service(db, current_user)
    cancelados = await service.cancelar_lote(lote_id, perm)
    return {"cancelados": cancelados}


# ---------------------------------------------------------------------------
# 6.7 POST /{comunicacion_id}/cancelar
# ---------------------------------------------------------------------------


@router.post(
    "/{comunicacion_id}/cancelar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancelar mensaje individual Pendiente",
)
async def cancelar_comunicacion(
    comunicacion_id: UUID,
    perm: Annotated[PermissionContext, Depends(require_permission("comunicacion:enviar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> None:
    service = _make_service(db, current_user)
    await service.cancelar_uno(comunicacion_id, perm)


# ---------------------------------------------------------------------------
# 6.8 POST /{comunicacion_id}/retry
# ---------------------------------------------------------------------------


@router.post(
    "/{comunicacion_id}/retry",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reintentar mensaje con Error",
)
async def retry_comunicacion(
    comunicacion_id: UUID,
    perm: Annotated[PermissionContext, Depends(require_permission("comunicacion:enviar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> None:
    service = _make_service(db, current_user)
    await service.retry_uno(comunicacion_id, perm)
