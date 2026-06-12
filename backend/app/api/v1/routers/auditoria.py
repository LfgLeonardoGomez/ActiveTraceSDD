"""Router de auditoría y métricas (C-19).

Endpoints bajo /api/auditoria/:
  5.2  GET /panel/acciones-por-dia              → AccionesPorDiaResponse
  5.3  GET /panel/comunicaciones-por-docente    → ComunicacionesPorDocenteResponse
  5.4  GET /panel/interacciones-por-docente-materia → InteraccionesPorDocenteMateriaResponse
  5.5  GET /panel/ultimas-acciones              → UltimasAccionesResponse
  5.6  GET /catalogo-acciones                  → CatalogoAccionesResponse
  5.7  GET /log                                → AuditLogPageResponse

Guard: require_permission("auditoria:ver") en todos los endpoints.
Fail-closed: sin permiso → 403.
Identidad y tenant_id EXCLUSIVAMENTE del JWT verificado.
Solo métodos GET — no existen endpoints de escritura (RN-23).
"""

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction
from app.core.dependencies import (
    CurrentUser,
    get_current_active_user,
    get_db,
    require_permission,
)
from app.schemas.auditoria import (
    AccionesPorDiaResponse,
    AuditLogPageResponse,
    CatalogoAccionesResponse,
    ComunicacionesPorDocenteResponse,
    InteraccionesPorDocenteMateriaResponse,
    UltimasAccionesResponse,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.auditoria_log_query_service import AuditoriaLogQueryService
from app.services.auditoria_panel_service import AuditoriaPanelService

router = APIRouter(
    prefix="/api/auditoria",
    tags=["auditoria"],
    responses={
        403: {"description": "Permiso denegado"},
        422: {"description": "Validación fallida"},
    },
)

_PANEL_MAX_LIMIT = 1000
_PANEL_DEFAULT_LIMIT = 200
_LOG_MAX_PAGE_SIZE = 200
_LOG_DEFAULT_PAGE_SIZE = 50


def _make_panel_service(
    db: AsyncSession, current_user: CurrentUser
) -> AuditoriaPanelService:
    return AuditoriaPanelService(
        db_session=db,
        tenant_id=current_user.tenant_id,
        current_user_id=current_user.real_actor_id,
    )


def _make_log_service(
    db: AsyncSession, current_user: CurrentUser
) -> AuditoriaLogQueryService:
    return AuditoriaLogQueryService(
        db_session=db,
        tenant_id=current_user.tenant_id,
        current_user_id=current_user.real_actor_id,
    )


# ---------------------------------------------------------------------------
# 5.2 GET /panel/acciones-por-dia
# ---------------------------------------------------------------------------


@router.get(
    "/panel/acciones-por-dia",
    response_model=AccionesPorDiaResponse,
    summary="Acciones de auditoría agrupadas por día (F9.1)",
)
async def get_acciones_por_dia(
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    materia_id: UUID | None = None,
    usuario_id: UUID | None = None,
    perm: Annotated[PermissionContext, Depends(require_permission("auditoria:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AccionesPorDiaResponse:
    service = _make_panel_service(db, current_user)
    return await service.get_acciones_por_dia(
        {
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "materia_id": materia_id,
            "usuario_id": usuario_id,
        },
        perm,
    )


# ---------------------------------------------------------------------------
# 5.3 GET /panel/comunicaciones-por-docente
# ---------------------------------------------------------------------------


@router.get(
    "/panel/comunicaciones-por-docente",
    response_model=ComunicacionesPorDocenteResponse,
    summary="Comunicaciones agrupadas por docente y estado (F9.1)",
)
async def get_comunicaciones_por_docente(
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    materia_id: UUID | None = None,
    usuario_id: UUID | None = None,
    perm: Annotated[PermissionContext, Depends(require_permission("auditoria:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ComunicacionesPorDocenteResponse:
    service = _make_panel_service(db, current_user)
    return await service.get_comunicaciones_por_docente(
        {
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "materia_id": materia_id,
            "usuario_id": usuario_id,
        },
        perm,
    )


# ---------------------------------------------------------------------------
# 5.4 GET /panel/interacciones-por-docente-materia
# ---------------------------------------------------------------------------


@router.get(
    "/panel/interacciones-por-docente-materia",
    response_model=InteraccionesPorDocenteMateriaResponse,
    summary="Interacciones agrupadas por docente, materia y acción (F9.1)",
)
async def get_interacciones_por_docente_materia(
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    materia_id: UUID | None = None,
    usuario_id: UUID | None = None,
    perm: Annotated[PermissionContext, Depends(require_permission("auditoria:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> InteraccionesPorDocenteMateriaResponse:
    service = _make_panel_service(db, current_user)
    return await service.get_interacciones_por_docente_materia(
        {
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "materia_id": materia_id,
            "usuario_id": usuario_id,
        },
        perm,
    )


# ---------------------------------------------------------------------------
# 5.5 GET /panel/ultimas-acciones
# ---------------------------------------------------------------------------


@router.get(
    "/panel/ultimas-acciones",
    response_model=UltimasAccionesResponse,
    summary="Últimas N acciones de auditoría, configurable (F9.1, D3)",
)
async def get_ultimas_acciones(
    limit: int = Query(default=_PANEL_DEFAULT_LIMIT, ge=1, le=_PANEL_MAX_LIMIT),
    materia_id: UUID | None = None,
    usuario_id: UUID | None = None,
    accion: AuditAction | None = None,
    perm: Annotated[PermissionContext, Depends(require_permission("auditoria:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> UltimasAccionesResponse:
    service = _make_panel_service(db, current_user)
    return await service.get_ultimas_acciones(
        {
            "limit": limit,
            "materia_id": materia_id,
            "usuario_id": usuario_id,
            "accion": accion,
        },
        perm,
    )


# ---------------------------------------------------------------------------
# 5.6 GET /catalogo-acciones
# ---------------------------------------------------------------------------


@router.get(
    "/catalogo-acciones",
    response_model=CatalogoAccionesResponse,
    summary="Catálogo de códigos de acción (enum AuditAction — RN-24)",
)
async def get_catalogo_acciones(
    perm: Annotated[PermissionContext, Depends(require_permission("auditoria:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> CatalogoAccionesResponse:
    service = _make_panel_service(db, current_user)
    return await service.get_catalogo_acciones()


# ---------------------------------------------------------------------------
# 5.7 GET /log
# ---------------------------------------------------------------------------


@router.get(
    "/log",
    response_model=AuditLogPageResponse,
    summary="Log completo de auditoría paginado con filtros (F9.2, RN-23/RN-24)",
)
async def get_log(
    fecha_desde: datetime | None = None,
    fecha_hasta: datetime | None = None,
    materia_id: UUID | None = None,
    usuario_id: UUID | None = None,
    accion: AuditAction | None = None,
    estado: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_LOG_DEFAULT_PAGE_SIZE, ge=1, le=_LOG_MAX_PAGE_SIZE),
    perm: Annotated[PermissionContext, Depends(require_permission("auditoria:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AuditLogPageResponse:
    service = _make_log_service(db, current_user)
    return await service.list_log(
        filtros={
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "materia_id": materia_id,
            "usuario_id": usuario_id,
            "accion": accion,
            "estado": estado,
        },
        permission_ctx=perm,
        page=page,
        page_size=page_size,
    )
