"""Router de análisis de atrasados y reportes (C-11).

Endpoints bajo /api/analisis/:
  5.1  GET /atrasados                → lista paginada de alumnos atrasados
  5.2  GET /ranking                  → ranking de actividades aprobadas
  5.3  GET /reporte-rapido           → métricas consolidadas
  5.4  GET /notas-finales            → notas finales calculadas
  5.5  GET /notas-finales/export     → export CSV de notas finales
  5.6  GET /tps-sin-corregir/export  → export CSV de TPs sin corregir
  5.7  GET /monitor/general          → monitor general (COORDINADOR/ADMIN)
  5.8  GET /monitor/general/export   → export CSV del monitor general
  5.9  GET /monitor/propio           → monitor propio (TUTOR/PROFESOR)
  5.10 GET /monitor/global           → monitor global con rango de fechas

Guard: require_permission("atrasados:ver") en todos los endpoints.
Identidad y tenant_id EXCLUSIVAMENTE del JWT verificado.
"""

import csv
import io
from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    get_current_active_user,
    get_db,
    require_permission,
)
from app.schemas.analisis import (
    AtrasadosResponseSchema,
    MonitorResponseSchema,
    NotaFinalItemSchema,
    RankingResponseSchema,
    ReporteRapidoSchema,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.analisis_service import AnalisisService

router = APIRouter(
    prefix="/api/analisis",
    tags=["analisis"],
    responses={
        403: {"description": "Permiso denegado"},
        422: {"description": "Validación fallida"},
    },
)

_MAX_PAGE_SIZE = 100
_DEFAULT_PAGE_SIZE = 50


def _validate_page_size(page_size: int) -> int:
    if page_size > _MAX_PAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"page_size no puede superar {_MAX_PAGE_SIZE}",
        )
    if page_size < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="page_size debe ser al menos 1",
        )
    return page_size


def _make_service(
    db: AsyncSession, current_user: CurrentUser
) -> AnalisisService:
    return AnalisisService(
        db_session=db,
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# 5.1 GET /atrasados
# ---------------------------------------------------------------------------


@router.get(
    "/atrasados",
    response_model=AtrasadosResponseSchema,
    summary="Listar alumnos atrasados de una asignación (paginado)",
)
async def get_atrasados(
    asignacion_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    perm: Annotated[PermissionContext, Depends(require_permission("atrasados:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AtrasadosResponseSchema:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    return await service.get_atrasados(asignacion_id, perm, page, page_size)


# ---------------------------------------------------------------------------
# 5.2 GET /ranking
# ---------------------------------------------------------------------------


@router.get(
    "/ranking",
    response_model=RankingResponseSchema,
    summary="Ranking de actividades aprobadas por asignación",
)
async def get_ranking(
    asignacion_id: UUID,
    perm: Annotated[PermissionContext, Depends(require_permission("atrasados:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> RankingResponseSchema:
    service = _make_service(db, current_user)
    return await service.get_ranking(asignacion_id, perm)


# ---------------------------------------------------------------------------
# 5.3 GET /reporte-rapido
# ---------------------------------------------------------------------------


@router.get(
    "/reporte-rapido",
    response_model=ReporteRapidoSchema,
    summary="Métricas consolidadas de una asignación",
)
async def get_reporte_rapido(
    asignacion_id: UUID,
    perm: Annotated[PermissionContext, Depends(require_permission("atrasados:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ReporteRapidoSchema:
    service = _make_service(db, current_user)
    return await service.get_reporte_rapido(asignacion_id, perm)


# ---------------------------------------------------------------------------
# 5.4 GET /notas-finales
# ---------------------------------------------------------------------------


@router.get(
    "/notas-finales",
    response_model=list[NotaFinalItemSchema],
    summary="Notas finales calculadas por alumno",
)
async def get_notas_finales(
    asignacion_id: UUID,
    actividades: list[str] = Query(default=[]),
    perm: Annotated[PermissionContext, Depends(require_permission("atrasados:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[NotaFinalItemSchema]:
    service = _make_service(db, current_user)
    return await service.get_notas_finales(asignacion_id, actividades, perm)


# ---------------------------------------------------------------------------
# 5.5 GET /notas-finales/export (CSV)
# ---------------------------------------------------------------------------


@router.get(
    "/notas-finales/export",
    summary="Exportar notas finales en CSV",
)
async def export_notas_finales(
    asignacion_id: UUID,
    actividades: list[str] = Query(default=[]),
    perm: Annotated[PermissionContext, Depends(require_permission("atrasados:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> StreamingResponse:
    service = _make_service(db, current_user)
    rows = await service.get_notas_finales(asignacion_id, actividades, perm)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["alumno", "email", "nota_final"])
    for row in rows:
        writer.writerow([row.alumno_nombre, row.alumno_email, row.nota_final])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="notas_finales_{asignacion_id}.csv"'
        },
    )


# ---------------------------------------------------------------------------
# 5.6 GET /tps-sin-corregir/export (CSV)
# ---------------------------------------------------------------------------


@router.get(
    "/tps-sin-corregir/export",
    summary="Exportar TPs sin corregir en CSV",
)
async def export_tps_sin_corregir(
    asignacion_id: UUID,
    perm: Annotated[PermissionContext, Depends(require_permission("atrasados:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> StreamingResponse:
    service = _make_service(db, current_user)
    rows = await service.get_tps_sin_corregir(asignacion_id, perm)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["alumno", "email", "actividad", "fecha_finalizacion"])
    for row in rows:
        writer.writerow([
            row["alumno_nombre"],
            row.get("alumno_email", ""),
            row["actividad"],
            row.get("fecha_finalizacion", ""),
        ])

    output.seek(0)

    extra_headers = {}
    if not rows:
        extra_headers["X-Sin-Datos-Finalizacion"] = "true"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="tps_sin_corregir_{asignacion_id}.csv"',
            **extra_headers,
        },
    )


# ---------------------------------------------------------------------------
# 5.7 GET /monitor/general
# ---------------------------------------------------------------------------


@router.get(
    "/monitor/general",
    response_model=MonitorResponseSchema,
    summary="Monitor general de actividades (COORDINADOR/ADMIN)",
)
async def get_monitor_general(
    materia_id: UUID | None = None,
    regional: str | None = None,
    comision: str | None = None,
    alumno: str | None = None,
    estado_actividad: str | None = None,
    criterio_clasificacion: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    perm: Annotated[PermissionContext, Depends(require_permission("atrasados:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> MonitorResponseSchema:
    _validate_page_size(page_size)
    filtros = {
        "materia_id": materia_id,
        "regional": regional,
        "comision": comision,
        "alumno": alumno,
        "estado_actividad": estado_actividad,
        "criterio_clasificacion": criterio_clasificacion,
    }
    service = _make_service(db, current_user)
    return await service.get_monitor_general(filtros, perm, page, page_size)


# ---------------------------------------------------------------------------
# 5.8 GET /monitor/general/export (CSV)
# ---------------------------------------------------------------------------


@router.get(
    "/monitor/general/export",
    summary="Exportar monitor general en CSV (sin límite de paginación)",
)
async def export_monitor_general(
    materia_id: UUID | None = None,
    regional: str | None = None,
    comision: str | None = None,
    alumno: str | None = None,
    estado_actividad: str | None = None,
    criterio_clasificacion: str | None = None,
    perm: Annotated[PermissionContext, Depends(require_permission("atrasados:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> StreamingResponse:
    filtros = {
        "materia_id": materia_id,
        "regional": regional,
        "comision": comision,
        "alumno": alumno,
        "estado_actividad": estado_actividad,
        "criterio_clasificacion": criterio_clasificacion,
    }
    service = _make_service(db, current_user)
    # Export: no limit (page=1, page_size=10000)
    monitor = await service.get_monitor_general(filtros, perm, page=1, page_size=10000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["alumno", "email", "materia", "actividades_aprobadas", "actividades_totales", "estado"])
    for item in monitor.items:
        writer.writerow([
            item.alumno_nombre,
            item.email,
            item.materia_nombre,
            item.actividades_aprobadas,
            item.actividades_totales,
            item.estado.value,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="monitor_general.csv"'
        },
    )


# ---------------------------------------------------------------------------
# 5.9 GET /monitor/propio
# ---------------------------------------------------------------------------


@router.get(
    "/monitor/propio",
    response_model=MonitorResponseSchema,
    summary="Monitor de seguimiento propio (TUTOR/PROFESOR)",
)
async def get_monitor_propio(
    alumno: str | None = None,
    email: str | None = None,
    comision: str | None = None,
    regional: str | None = None,
    actividad_id: str | None = None,
    min_actividades_cumplidas: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    perm: Annotated[PermissionContext, Depends(require_permission("atrasados:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> MonitorResponseSchema:
    _validate_page_size(page_size)
    filtros = {
        "alumno": alumno,
        "email": email,
        "comision": comision,
        "regional": regional,
        "actividad_id": actividad_id,
        "min_actividades_cumplidas": min_actividades_cumplidas,
    }
    service = _make_service(db, current_user)
    return await service.get_monitor_propio(filtros, perm, page, page_size)


# ---------------------------------------------------------------------------
# 5.10 GET /monitor/global
# ---------------------------------------------------------------------------


@router.get(
    "/monitor/global",
    response_model=MonitorResponseSchema,
    summary="Monitor global de seguimiento con rango de fechas (COORDINADOR/ADMIN)",
)
async def get_monitor_global(
    materia_id: UUID | None = None,
    regional: str | None = None,
    comision: str | None = None,
    alumno: str | None = None,
    estado_actividad: str | None = None,
    criterio_clasificacion: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    perm: Annotated[PermissionContext, Depends(require_permission("atrasados:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> MonitorResponseSchema:
    _validate_page_size(page_size)
    filtros = {
        "materia_id": materia_id,
        "regional": regional,
        "comision": comision,
        "alumno": alumno,
        "estado_actividad": estado_actividad,
        "criterio_clasificacion": criterio_clasificacion,
    }

    fd = datetime.combine(fecha_desde, datetime.min.time()) if fecha_desde else None
    fh = datetime.combine(fecha_hasta, datetime.max.time()) if fecha_hasta else None

    service = _make_service(db, current_user)
    return await service.get_monitor_global(filtros, fd, fh, perm, page, page_size)
