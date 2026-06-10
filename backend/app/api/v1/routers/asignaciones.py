"""Router de asignaciones de rol en contexto académico (C-07).

Todos los endpoints protegidos por require_permission("equipos:asignar").
Identidad y tenant_id provienen EXCLUSIVAMENTE del JWT verificado.
Fail-closed: sin permiso → 403 (sin excepciones).

Endpoints:
- POST   /api/v1/asignaciones          → crear asignación (201)
- GET    /api/v1/asignaciones          → listar asignaciones paginadas
- GET    /api/v1/asignaciones/{id}     → detalle de asignación
- PUT    /api/v1/asignaciones/{id}     → actualizar (parcial)
- DELETE /api/v1/asignaciones/{id}     → soft delete (204)
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
from app.schemas.asignaciones import (
    AsignacionCreate,
    AsignacionRead,
    AsignacionUpdate,
    PaginatedAsignacionesResponse,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.asignaciones import AsignacionService

_common_responses = {
    403: {"description": "Permiso denegado"},
    404: {"description": "Asignación o recurso FK no encontrado"},
    422: {"description": "Validación fallida"},
}

router = APIRouter(
    prefix="/api/v1/asignaciones",
    tags=["asignaciones"],
    responses=_common_responses,
)


@router.post(
    "",
    response_model=AsignacionRead,
    status_code=status.HTTP_201_CREATED,
)
async def crear_asignacion(
    body: AsignacionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("equipos:asignar"))],
) -> AsignacionRead:
    """Crea una asignación de rol en el tenant del actor autenticado."""
    service = AsignacionService(db, current_user.tenant_id)
    asig = await service.crear_asignacion(
        usuario_id=body.usuario_id,
        rol=body.rol,
        desde=body.desde,
        hasta=body.hasta,
        materia_id=body.materia_id,
        carrera_id=body.carrera_id,
        cohorte_id=body.cohorte_id,
        comisiones=body.comisiones,
        responsable_id=body.responsable_id,
    )
    return AsignacionRead.model_validate(asig)


@router.get(
    "",
    response_model=PaginatedAsignacionesResponse,
)
async def listar_asignaciones(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("equipos:asignar"))],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    usuario_id: Annotated[UUID | None, Query()] = None,
    rol: Annotated[str | None, Query()] = None,
    materia_id: Annotated[UUID | None, Query()] = None,
    carrera_id: Annotated[UUID | None, Query()] = None,
    cohorte_id: Annotated[UUID | None, Query()] = None,
    incluir_vencidas: Annotated[bool, Query()] = True,
) -> PaginatedAsignacionesResponse:
    """Lista asignaciones del tenant con filtros opcionales y paginación."""
    service = AsignacionService(db, current_user.tenant_id)
    items, total = await service.listar_asignaciones(
        limit=limit,
        offset=offset,
        usuario_id=usuario_id,
        rol=rol,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        incluir_vencidas=incluir_vencidas,
    )
    return PaginatedAsignacionesResponse(
        items=[AsignacionRead.model_validate(a) for a in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{asignacion_id}",
    response_model=AsignacionRead,
)
async def obtener_asignacion(
    asignacion_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("equipos:asignar"))],
) -> AsignacionRead:
    """Obtiene detalle de una asignación por ID."""
    service = AsignacionService(db, current_user.tenant_id)
    asig = await service.obtener_asignacion(asignacion_id)
    return AsignacionRead.model_validate(asig)


@router.put(
    "/{asignacion_id}",
    response_model=AsignacionRead,
)
async def actualizar_asignacion(
    asignacion_id: UUID,
    body: AsignacionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("equipos:asignar"))],
) -> AsignacionRead:
    """Actualiza campos de una asignación (parcial — solo los campos enviados)."""
    service = AsignacionService(db, current_user.tenant_id)
    data = body.model_dump(exclude_unset=True)
    asig = await service.actualizar_asignacion(asignacion_id, data)
    return AsignacionRead.model_validate(asig)


@router.delete(
    "/{asignacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def eliminar_asignacion(
    asignacion_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("equipos:asignar"))],
) -> None:
    """Soft delete de asignación (setea deleted_at)."""
    service = AsignacionService(db, current_user.tenant_id)
    await service.eliminar_asignacion(asignacion_id)
