"""Router de encuentros y slots (C-13).

Endpoints:
- POST /api/v1/encuentros/slots          → crear slot (encuentros:gestionar)
- POST /api/v1/encuentros/instancias     → crear instancia única (encuentros:gestionar)
- GET  /api/v1/encuentros/slots          → listar slots (encuentros:gestionar)
- GET  /api/v1/encuentros/slots/{id}     → obtener slot (encuentros:gestionar)
- PUT  /api/v1/encuentros/slots/{id}     → actualizar slot (encuentros:gestionar)
- DELETE /api/v1/encuentros/slots/{id}   → soft-delete slot (encuentros:gestionar)
- GET  /api/v1/encuentros/instancias     → listar instancias (encuentros:gestionar)
- PUT  /api/v1/encuentros/instancias/{id}→ editar instancia (encuentros:gestionar)
- GET  /api/v1/encuentros/bloque-html    → generar bloque HTML/Markdown
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
from app.schemas.encuentros import (
    BloqueHtmlParams,
    InstanciaCreate,
    InstanciaFilterParams,
    InstanciaRead,
    InstanciaUpdate,
    PaginatedInstanciaResponse,
    PaginatedSlotResponse,
    SlotCreate,
    SlotRead,
    SlotUpdate,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.encuentros import EncuentroService

_common_responses = {
    403: {"description": "Permiso denegado"},
    404: {"description": "Slot o instancia no encontrado"},
    422: {"description": "Validación fallida"},
}

router = APIRouter(
    prefix="/api/v1/encuentros",
    tags=["encuentros"],
    responses=_common_responses,
)


# ------------------------------------------------------------------
# Slots
# ------------------------------------------------------------------

@router.post(
    "/slots",
    response_model=SlotRead,
    status_code=status.HTTP_201_CREATED,
)
async def crear_slot(
    body: SlotCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("encuentros:gestionar"))],
) -> SlotRead:
    """Crea un slot de encuentro recurrente y genera instancias."""
    service = EncuentroService(db, current_user.tenant_id)
    slot = await service.crear_slot(data=body, actor_id=current_user.real_actor_id)
    return SlotRead.model_validate(slot)


@router.get(
    "/slots",
    response_model=PaginatedSlotResponse,
)
async def listar_slots(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("encuentros:gestionar"))],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    materia_id: Annotated[UUID | None, Query()] = None,
) -> PaginatedSlotResponse:
    """Lista slots de encuentro del tenant."""
    service = EncuentroService(db, current_user.tenant_id)
    return await service.listar_slots(
        materia_id=materia_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/slots/{slot_id}",
    response_model=SlotRead,
)
async def obtener_slot(
    slot_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("encuentros:gestionar"))],
) -> SlotRead:
    """Obtiene un slot por ID."""
    service = EncuentroService(db, current_user.tenant_id)
    slot = await service.obtener_slot(slot_id)
    return SlotRead.model_validate(slot)


@router.put(
    "/slots/{slot_id}",
    response_model=SlotRead,
)
async def actualizar_slot(
    slot_id: UUID,
    body: SlotUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("encuentros:gestionar"))],
) -> SlotRead:
    """Actualiza un slot (no afecta instancias existentes)."""
    service = EncuentroService(db, current_user.tenant_id)
    slot = await service.actualizar_slot(
        slot_id=slot_id,
        data=body,
        actor_id=current_user.real_actor_id,
    )
    return SlotRead.model_validate(slot)


@router.delete(
    "/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def eliminar_slot(
    slot_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("encuentros:gestionar"))],
) -> None:
    """Soft-delete de slot y cascada a instancias."""
    service = EncuentroService(db, current_user.tenant_id)
    await service.eliminar_slot(slot_id=slot_id, actor_id=current_user.real_actor_id)


# ------------------------------------------------------------------
# Instancias
# ------------------------------------------------------------------

@router.post(
    "/instancias",
    response_model=InstanciaRead,
    status_code=status.HTTP_201_CREATED,
)
async def crear_instancia_unica(
    body: InstanciaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("encuentros:gestionar"))],
) -> InstanciaRead:
    """Crea una instancia de encuentro independiente (sin slot)."""
    service = EncuentroService(db, current_user.tenant_id)
    instancia = await service.crear_instancia_unica(
        data=body,
        actor_id=current_user.real_actor_id,
    )
    return InstanciaRead.model_validate(instancia)


@router.get(
    "/instancias",
    response_model=PaginatedInstanciaResponse,
)
async def listar_instancias(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("encuentros:gestionar"))],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    materia_id: Annotated[UUID | None, Query()] = None,
    slot_id: Annotated[UUID | None, Query()] = None,
    estado: Annotated[str | None, Query()] = None,
    fecha_desde: Annotated[date | None, Query()] = None,
    fecha_hasta: Annotated[date | None, Query()] = None,
) -> PaginatedInstanciaResponse:
    """Lista instancias de encuentro con filtros."""
    service = EncuentroService(db, current_user.tenant_id)
    filters = InstanciaFilterParams(
        materia_id=materia_id,
        slot_id=slot_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return await service.listar_instancias(
        filters=filters,
        limit=limit,
        offset=offset,
    )


@router.put(
    "/instancias/{instancia_id}",
    response_model=InstanciaRead,
)
async def editar_instancia(
    instancia_id: UUID,
    body: InstanciaUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("encuentros:gestionar"))],
) -> InstanciaRead:
    """Edita una instancia de encuentro."""
    service = EncuentroService(db, current_user.tenant_id)
    instancia = await service.editar_instancia(
        instancia_id=instancia_id,
        data=body,
        actor_id=current_user.real_actor_id,
    )
    return InstanciaRead.model_validate(instancia)


# ------------------------------------------------------------------
# Bloque HTML / Markdown
# ------------------------------------------------------------------

@router.get(
    "/bloque-html",
    response_model=str,
)
async def bloque_html(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("encuentros:gestionar"))],
    materia_id: Annotated[UUID, Query()],
    slot_id: Annotated[UUID | None, Query()] = None,
    formato: Annotated[str, Query(pattern="^(html|markdown)$")] = "html",
) -> str:
    """Genera un bloque HTML o Markdown con las instancias programadas."""
    service = EncuentroService(db, current_user.tenant_id)
    params = BloqueHtmlParams(
        materia_id=materia_id,
        slot_id=slot_id,
        formato=formato,
    )
    return await service.generar_bloque_html(params)
