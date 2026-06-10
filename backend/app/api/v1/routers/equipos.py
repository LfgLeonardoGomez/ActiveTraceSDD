"""Router de equipos docentes (C-08).

Endpoints:
- GET  /api/v1/equipos/mis-equipos      → mis asignaciones (auth only)
- GET  /api/v1/equipos/equipo           → equipo por contexto (equipos:asignar)
- POST /api/v1/equipos/asignacion-masiva → bulk assign (equipos:asignar)
- POST /api/v1/equipos/clonar           → clone team (equipos:asignar)
- PUT  /api/v1/equipos/{materia_id}/{carrera_id}/{cohorte_id}/vigencia
                                         → batch vigencia (equipos:asignar)
- GET  /api/v1/equipos/exportar          → CSV/XLSX export (equipos:asignar)
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    get_current_active_user,
    get_db,
    require_permission,
)
from app.schemas.equipos import (
    ActualizarVigenciaRequest,
    ActualizarVigenciaResponse,
    AsignacionMasivaRequest,
    AsignacionMasivaResponse,
    ClonarEquipoRequest,
    ClonarEquipoResponse,
    EquipoFilterParams,
    PaginatedEquipoResponse,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.equipos import EquipoService

_common_responses = {
    403: {"description": "Permiso denegado"},
    404: {"description": "Equipo o recurso no encontrado"},
    422: {"description": "Validación fallida"},
}

router = APIRouter(
    prefix="/api/v1/equipos",
    tags=["equipos"],
    responses=_common_responses,
)


# ------------------------------------------------------------------
# Mis equipos (auth only — sin require_permission)
# ------------------------------------------------------------------

@router.get(
    "/mis-equipos",
    response_model=PaginatedEquipoResponse,
)
async def mis_equipos(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    materia_id: Annotated[UUID | None, Query()] = None,
    carrera_id: Annotated[UUID | None, Query()] = None,
    cohorte_id: Annotated[UUID | None, Query()] = None,
    estado_vigencia: Annotated[str | None, Query()] = None,
) -> PaginatedEquipoResponse:
    """Lista las asignaciones del usuario autenticado con contexto académico."""
    service = EquipoService(db, current_user.tenant_id)
    filters = EquipoFilterParams(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        estado_vigencia=estado_vigencia,
    )
    return await service.mis_equipos(
        current_user=current_user,
        filters=filters,
        limit=limit,
        offset=offset,
    )


# ------------------------------------------------------------------
# Equipo por contexto (equipos:asignar)
# ------------------------------------------------------------------

@router.get(
    "/equipo",
    response_model=PaginatedEquipoResponse,
)
async def listar_equipo(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("equipos:asignar"))],
    materia_id: Annotated[UUID, Query()],
    carrera_id: Annotated[UUID, Query()],
    cohorte_id: Annotated[UUID, Query()],
    estado_vigencia: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedEquipoResponse:
    """Lista asignaciones de un equipo por contexto académico."""
    service = EquipoService(db, current_user.tenant_id)
    return await service.list_equipo(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        estado_vigencia=estado_vigencia,
        limit=limit,
        offset=offset,
    )


# ------------------------------------------------------------------
# Asignación masiva (equipos:asignar)
# ------------------------------------------------------------------

@router.post(
    "/asignacion-masiva",
    response_model=AsignacionMasivaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def asignacion_masiva(
    body: AsignacionMasivaRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("equipos:asignar"))],
) -> AsignacionMasivaResponse:
    """Asigna masivamente docentes a un equipo."""
    service = EquipoService(db, current_user.tenant_id)
    return await service.asignacion_masiva(data=body, current_user=current_user)


# ------------------------------------------------------------------
# Clonar equipo (equipos:asignar)
# ------------------------------------------------------------------

@router.post(
    "/clonar",
    response_model=ClonarEquipoResponse,
)
async def clonar_equipo(
    body: ClonarEquipoRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("equipos:asignar"))],
) -> ClonarEquipoResponse:
    """Clona asignaciones vigentes de un equipo a otra cohorte."""
    service = EquipoService(db, current_user.tenant_id)
    return await service.clonar_equipo(data=body, current_user=current_user)


# ------------------------------------------------------------------
# Actualizar vigencia (equipos:asignar)
# ------------------------------------------------------------------

@router.put(
    "/{materia_id}/{carrera_id}/{cohorte_id}/vigencia",
    response_model=ActualizarVigenciaResponse,
)
async def actualizar_vigencia(
    materia_id: UUID,
    carrera_id: UUID,
    cohorte_id: UUID,
    body: ActualizarVigenciaRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("equipos:asignar"))],
) -> ActualizarVigenciaResponse:
    """Actualiza vigencia de todas las asignaciones vigentes del equipo."""
    service = EquipoService(db, current_user.tenant_id)
    return await service.actualizar_vigencia(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        data=body,
        current_user=current_user,
    )


# ------------------------------------------------------------------
# Exportar equipo (equipos:asignar)
# ------------------------------------------------------------------

@router.get(
    "/exportar",
)
async def exportar_equipo(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("equipos:asignar"))],
    materia_id: Annotated[UUID, Query()],
    carrera_id: Annotated[UUID, Query()],
    cohorte_id: Annotated[UUID, Query()],
    format: Annotated[str, Query(pattern="^(csv|xlsx)$")] = "csv",
    include_pii: Annotated[bool, Query()] = False,
) -> StreamingResponse:
    """Exporta equipo a CSV o XLSX."""
    service = EquipoService(db, current_user.tenant_id)
    return await service.exportar_equipo(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        format=format,
        include_pii=include_pii,
        current_user=current_user,
    )
