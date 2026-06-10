"""Router de guardias (C-13).

Endpoints:
- POST /api/v1/guardias              → registrar guardia (guardias:registrar)
- GET  /api/v1/guardias               → listar guardias (encuentros:gestionar)
- GET  /api/v1/guardias/{id}          → obtener guardia (guardias:registrar)
- GET  /api/v1/guardias/exportar      → exportar guardias (encuentros:gestionar)
"""

from datetime import date
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
from app.schemas.guardias import (
    ExportarGuardiasParams,
    GuardiaCreate,
    GuardiaFilterParams,
    GuardiaRead,
    GuardiaUpdate,
    PaginatedGuardiaResponse,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.guardias import GuardiaService

_common_responses = {
    403: {"description": "Permiso denegado"},
    404: {"description": "Guardia no encontrada"},
    422: {"description": "Validación fallida"},
}

router = APIRouter(
    prefix="/api/v1/guardias",
    tags=["guardias"],
    responses=_common_responses,
)


# ------------------------------------------------------------------
# Registro
# ------------------------------------------------------------------

@router.post(
    "",
    response_model=GuardiaRead,
    status_code=status.HTTP_201_CREATED,
)
async def registrar_guardia(
    body: GuardiaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("guardias:registrar"))],
) -> GuardiaRead:
    """Registra una guardia de atención a alumnos."""
    service = GuardiaService(db, current_user.tenant_id)
    guardia = await service.registrar_guardia(
        data=body,
        actor_id=current_user.real_actor_id,
    )
    return GuardiaRead.model_validate(guardia)


# ------------------------------------------------------------------
# Listado
# ------------------------------------------------------------------

@router.get(
    "",
    response_model=PaginatedGuardiaResponse,
)
async def listar_guardias(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("encuentros:gestionar"))],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    materia_id: Annotated[UUID | None, Query()] = None,
    tutor_id: Annotated[UUID | None, Query()] = None,
    estado: Annotated[str | None, Query()] = None,
    fecha_desde: Annotated[date | None, Query()] = None,
    fecha_hasta: Annotated[date | None, Query()] = None,
) -> PaginatedGuardiaResponse:
    """Lista guardias del tenant con filtros y paginación.

    Scope:
    - COORDINADOR / ADMIN: ven todas las guardias.
    - TUTOR / PROFESOR: solo las propias.
    """
    service = GuardiaService(db, current_user.tenant_id)
    filters = GuardiaFilterParams(
        materia_id=materia_id,
        tutor_id=tutor_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return await service.listar_guardias(
        filters=filters,
        limit=limit,
        offset=offset,
        current_user_id=current_user.id,
        current_user_roles=current_user.roles,
    )


# ------------------------------------------------------------------
# Detalle
# ------------------------------------------------------------------

@router.get(
    "/{guardia_id}",
    response_model=GuardiaRead,
)
async def obtener_guardia(
    guardia_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("guardias:registrar"))],
) -> GuardiaRead:
    """Obtiene una guardia por ID."""
    service = GuardiaService(db, current_user.tenant_id)
    guardia = await service.obtener_guardia(guardia_id)
    return GuardiaRead.model_validate(guardia)


# ------------------------------------------------------------------
# Exportación
# ------------------------------------------------------------------

@router.get(
    "/exportar",
)
async def exportar_guardias(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("encuentros:gestionar"))],
    formato: Annotated[str, Query(pattern="^(csv|xlsx)$")] = "csv",
    materia_id: Annotated[UUID | None, Query()] = None,
    tutor_id: Annotated[UUID | None, Query()] = None,
    estado: Annotated[str | None, Query()] = None,
    fecha_desde: Annotated[date | None, Query()] = None,
    fecha_hasta: Annotated[date | None, Query()] = None,
):
    """Exporta guardias a CSV o XLSX.

    Scope:
    - COORDINADOR / ADMIN: exportan todas las guardias.
    - TUTOR / PROFESOR: solo las propias.
    """
    service = GuardiaService(db, current_user.tenant_id)
    params = ExportarGuardiasParams(
        formato=formato,
        materia_id=materia_id,
        tutor_id=tutor_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return await service.exportar_guardias(
        params=params,
        current_user_id=current_user.id,
        current_user_roles=current_user.roles,
    )


# ------------------------------------------------------------------
# Actualización (opcional, no requerida por tasks.md pero útil)
# ------------------------------------------------------------------

@router.put(
    "/{guardia_id}",
    response_model=GuardiaRead,
)
async def actualizar_guardia(
    guardia_id: UUID,
    body: GuardiaUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("guardias:registrar"))],
) -> GuardiaRead:
    """Actualiza una guardia."""
    service = GuardiaService(db, current_user.tenant_id)
    guardia = await service.actualizar_guardia(
        guardia_id=guardia_id,
        data=body,
        actor_id=current_user.real_actor_id,
    )
    return GuardiaRead.model_validate(guardia)
