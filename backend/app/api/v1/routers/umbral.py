"""Router de umbral de aprobación (C-10).

Endpoints:
- GET  /api/v1/umbral/{materia_id}  → obtener umbral vigente (o default 60%)
- PUT  /api/v1/umbral/{materia_id}  → configurar umbral + recalcular aprobado

Permisos:
  calificaciones:ver      → GET
  calificaciones:importar → PUT
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
from app.schemas.umbral import UmbralMateriaRead, UmbralMateriaUpsert
from app.services.umbral_service import UmbralService

_common_responses = {
    403: {"description": "Permiso denegado"},
    422: {"description": "Validación fallida"},
}

router = APIRouter(
    prefix="/api/v1/umbral",
    tags=["umbral"],
    responses=_common_responses,
)


@router.get(
    "/{materia_id}",
    response_model=UmbralMateriaRead,
    summary="Obtener umbral de aprobación de una materia",
)
async def get_umbral(
    materia_id: UUID,
    _perm: Annotated[object, Depends(require_permission("calificaciones:ver"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UmbralMateriaRead:
    """Devuelve el umbral configurado, o 60% / defaults si no existe configuración."""
    service = UmbralService(db, current_user.tenant_id)
    return await service.get_umbral(materia_id, current_user)


@router.put(
    "/{materia_id}",
    response_model=UmbralMateriaRead,
    summary="Configurar umbral de aprobación de una materia",
)
async def upsert_umbral(
    materia_id: UUID,
    body: UmbralMateriaUpsert,
    _perm: Annotated[object, Depends(require_permission("calificaciones:importar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UmbralMateriaRead:
    """Crea o actualiza el umbral y recalcula aprobado en batch para las calificaciones del docente."""
    service = UmbralService(db, current_user.tenant_id)
    return await service.upsert_umbral(materia_id, body, current_user)
