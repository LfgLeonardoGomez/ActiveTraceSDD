"""Router de evaluaciones y coloquios (C-14).

Endpoints bajo /api/coloquios/:
  POST /                          → crear convocatoria (gestionar)
  GET  /                          → listar convocatorias con métricas (ver)
  GET  /metricas                  → panel de métricas globales (ver)
  GET  /agenda                    → agenda consolidada (gestionar)
  PATCH /{id}                     → editar convocatoria (gestionar)
  POST /{id}/candidatos           → importar candidatos (gestionar)
  GET  /{id}/candidatos           → listar candidatos (ver)
  POST /{id}/reservas             → reservar turno (reservar)
  GET  /{id}/reservas             → listar reservas (ver)
  DELETE /{id}/reservas/{rid}     → cancelar reserva (reservar o gestionar)
  POST /{id}/resultados           → registrar resultado (gestionar)
  GET  /{id}/resultados           → listar resultados (ver)
  GET  /{id}/resultados/export    → export CSV de resultados (ver)

Guards: require_permission por endpoint. Identidad EXCLUSIVAMENTE del JWT.
"""

import csv
import io
from datetime import datetime
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
from app.schemas.evaluacion import (
    AgendaResponseSchema,
    CandidatosImportResponseSchema,
    CandidatosImportSchema,
    EvaluacionCreateSchema,
    EvaluacionResponseSchema,
    EvaluacionUpdateSchema,
    MetricasColoquiosSchema,
    ReservaCreateSchema,
    ReservaResponseSchema,
    ReservasListResponseSchema,
    ResultadoUpsertSchema,
    ResultadoResponseSchema,
    ResultadosListResponseSchema,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.evaluacion_service import EvaluacionService

router = APIRouter(
    prefix="/api/coloquios",
    tags=["coloquios"],
    responses={
        403: {"description": "Permiso denegado"},
        404: {"description": "No encontrado"},
        409: {"description": "Conflicto (cupo, duplicado, estado)"},
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


def _make_service(db: AsyncSession, current_user: CurrentUser) -> EvaluacionService:
    return EvaluacionService(
        db_session=db,
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# POST / — Crear convocatoria
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=EvaluacionResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear convocatoria de evaluación",
)
async def crear_convocatoria(
    body: EvaluacionCreateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EvaluacionResponseSchema:
    service = _make_service(db, current_user)
    return await service.crear_convocatoria(body.model_dump())


# ---------------------------------------------------------------------------
# GET / — Listar convocatorias
# ---------------------------------------------------------------------------

@router.get(
    "/",
    summary="Listar convocatorias del tenant con métricas",
)
async def list_convocatorias(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    return await service.list_convocatorias(page, page_size)


# ---------------------------------------------------------------------------
# GET /metricas — Panel de métricas globales
# ---------------------------------------------------------------------------

@router.get(
    "/metricas",
    response_model=MetricasColoquiosSchema,
    summary="Panel de métricas globales de coloquios",
)
async def get_metricas(
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:ver"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MetricasColoquiosSchema:
    service = _make_service(db, current_user)
    return await service.get_metricas_globales()


# ---------------------------------------------------------------------------
# GET /agenda — Agenda consolidada (solo COORDINADOR/ADMIN)
# ---------------------------------------------------------------------------

@router.get(
    "/agenda",
    response_model=AgendaResponseSchema,
    summary="Agenda consolidada de reservas activas (COORDINADOR/ADMIN)",
)
async def get_agenda(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    evaluacion_id: UUID | None = Query(default=None),
    fecha_desde: datetime | None = Query(default=None),
    fecha_hasta: datetime | None = Query(default=None),
    materia_id: UUID | None = Query(default=None),
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:gestionar"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> AgendaResponseSchema:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    return await service.get_agenda_global(
        page=page,
        page_size=page_size,
        evaluacion_id=evaluacion_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        materia_id=materia_id,
    )


# ---------------------------------------------------------------------------
# PATCH /{id} — Editar convocatoria
# ---------------------------------------------------------------------------

@router.patch(
    "/{evaluacion_id}",
    response_model=EvaluacionResponseSchema,
    summary="Editar campos editables de una convocatoria",
)
async def update_convocatoria(
    evaluacion_id: UUID,
    body: EvaluacionUpdateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EvaluacionResponseSchema:
    service = _make_service(db, current_user)
    return await service.update_convocatoria(evaluacion_id, body.model_dump())


# ---------------------------------------------------------------------------
# POST /{id}/candidatos — Importar candidatos
# ---------------------------------------------------------------------------

@router.post(
    "/{evaluacion_id}/candidatos",
    response_model=CandidatosImportResponseSchema,
    summary="Importar padrón de candidatos habilitados",
)
async def importar_candidatos(
    evaluacion_id: UUID,
    body: CandidatosImportSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CandidatosImportResponseSchema:
    service = _make_service(db, current_user)
    return await service.importar_candidatos(evaluacion_id, body.alumno_ids)


# ---------------------------------------------------------------------------
# GET /{id}/candidatos — Listar candidatos
# ---------------------------------------------------------------------------

@router.get(
    "/{evaluacion_id}/candidatos",
    summary="Listar candidatos habilitados de una convocatoria",
)
async def get_candidatos(
    evaluacion_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:ver"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list:
    service = _make_service(db, current_user)
    return await service._repo.get_candidatos(evaluacion_id)


# ---------------------------------------------------------------------------
# POST /{id}/reservas — Reservar turno (ALUMNO)
# ---------------------------------------------------------------------------

@router.post(
    "/{evaluacion_id}/reservas",
    response_model=ReservaResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Reservar turno en una convocatoria",
)
async def crear_reserva(
    evaluacion_id: UUID,
    body: ReservaCreateSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:reservar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReservaResponseSchema:
    service = _make_service(db, current_user)
    return await service.crear_reserva(evaluacion_id, current_user.id, body.fecha_hora)


# ---------------------------------------------------------------------------
# GET /{id}/reservas — Listar reservas (ver)
# ---------------------------------------------------------------------------

@router.get(
    "/{evaluacion_id}/reservas",
    response_model=ReservasListResponseSchema,
    summary="Listar reservas de una convocatoria",
)
async def get_reservas(
    evaluacion_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ReservasListResponseSchema:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    return await service.get_reservas(evaluacion_id, page, page_size)


# ---------------------------------------------------------------------------
# DELETE /{id}/reservas/{rid} — Cancelar reserva
# ---------------------------------------------------------------------------

async def _require_cancel_permission(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> bool:
    """Permite GESTIONAR (True) o RESERVAR (False). 403 si ninguno."""
    from app.services.permission_service import PermissionService
    svc = PermissionService(db, current_user.tenant_id)
    effective = await svc.resolve_effective_permissions(current_user.roles)
    perms = {code for code, _ in effective}
    if "coloquios:gestionar" in perms:
        return True
    if "coloquios:reservar" in perms:
        return False
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Permiso denegado",
    )


@router.delete(
    "/{evaluacion_id}/reservas/{reserva_id}",
    response_model=ReservaResponseSchema,
    summary="Cancelar una reserva (propia o por coordinación)",
)
async def cancelar_reserva(
    evaluacion_id: UUID,
    reserva_id: UUID,
    puede_gestionar: Annotated[bool, Depends(_require_cancel_permission)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReservaResponseSchema:
    service = _make_service(db, current_user)
    return await service.cancelar_reserva(
        evaluacion_id=evaluacion_id,
        reserva_id=reserva_id,
        solicitante_id=current_user.id,
        puede_gestionar=puede_gestionar,
    )


# ---------------------------------------------------------------------------
# POST /{id}/resultados — Registrar resultado
# ---------------------------------------------------------------------------

@router.post(
    "/{evaluacion_id}/resultados",
    response_model=ResultadoResponseSchema,
    summary="Registrar o actualizar resultado de un alumno",
)
async def registrar_resultado(
    evaluacion_id: UUID,
    body: ResultadoUpsertSchema,
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:gestionar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResultadoResponseSchema:
    service = _make_service(db, current_user)
    return await service.registrar_resultado(evaluacion_id, body.alumno_id, body.nota_final)


# ---------------------------------------------------------------------------
# GET /{id}/resultados — Listar resultados
# ---------------------------------------------------------------------------

@router.get(
    "/{evaluacion_id}/resultados",
    response_model=ResultadosListResponseSchema,
    summary="Registro académico consolidado de la convocatoria",
)
async def get_resultados(
    evaluacion_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1),
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ResultadosListResponseSchema:
    _validate_page_size(page_size)
    service = _make_service(db, current_user)
    return await service.get_resultados(evaluacion_id, page, page_size)


# ---------------------------------------------------------------------------
# GET /{id}/resultados/export — Export CSV
# ---------------------------------------------------------------------------

@router.get(
    "/{evaluacion_id}/resultados/export",
    summary="Exportar resultados de la convocatoria a CSV",
)
async def export_resultados_csv(
    evaluacion_id: UUID,
    _perm: Annotated[PermissionContext, Depends(require_permission("coloquios:ver"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    from app.repositories.evaluacion_repository import EvaluacionRepository

    repo = EvaluacionRepository(db, current_user.tenant_id)
    rows = await repo.get_resultados_csv_rows(evaluacion_id)

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["alumno_nombre", "alumno_email", "nota_final"],
    )
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=resultados_{evaluacion_id}.csv"
        },
    )
