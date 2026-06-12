"""Router de MateriaGrupoPlus (C-18).

Endpoints:
- POST   /api/v1/liquidaciones/materia-grupo-plus          → crear
- GET    /api/v1/liquidaciones/materia-grupo-plus          → listar
- GET    /api/v1/liquidaciones/materia-grupo-plus/{id}     → obtener
- PATCH  /api/v1/liquidaciones/materia-grupo-plus/{id}     → actualizar
- DELETE /api/v1/liquidaciones/materia-grupo-plus/{id}     → soft delete

Permiso requerido: liquidaciones:configurar-salarios
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_active_user, get_db, require_permission
from app.modules.liquidaciones.exceptions import VigenciaSolapadaError
from app.modules.liquidaciones.schemas.materia_grupo_plus import (
    MateriaGrupoPlusCreate,
    MateriaGrupoPlusRead,
    MateriaGrupoPlusUpdate,
)
from app.modules.liquidaciones.services.materia_grupo_plus_service import MateriaGrupoPlusService

router = APIRouter(
    prefix="/api/v1/liquidaciones/materia-grupo-plus",
    tags=["liquidaciones-grilla"],
    responses={
        403: {"description": "Permiso denegado"},
        409: {"description": "Vigencia solapada"},
        422: {"description": "Validación fallida"},
    },
)


@router.post(
    "",
    response_model=MateriaGrupoPlusRead,
    status_code=status.HTTP_201_CREATED,
    summary="Asignar grupo de Plus a materia",
)
async def crear_materia_grupo_plus(
    body: MateriaGrupoPlusCreate,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MateriaGrupoPlusRead:
    service = MateriaGrupoPlusService(db, current_user.tenant_id)
    try:
        return await service.crear(body, current_user)
    except VigenciaSolapadaError as e:
        raise HTTPException(status_code=409, detail={"error": "vigencia_solapada", "detalle": str(e)})


@router.get(
    "",
    response_model=list[MateriaGrupoPlusRead],
    summary="Listar MateriaGrupoPlus activos",
)
async def listar_materia_grupo_plus(
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MateriaGrupoPlusRead]:
    service = MateriaGrupoPlusService(db, current_user.tenant_id)
    return await service.listar()


@router.get(
    "/{mgp_id}",
    response_model=MateriaGrupoPlusRead,
    summary="Obtener MateriaGrupoPlus por ID",
)
async def obtener_materia_grupo_plus(
    mgp_id: UUID,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MateriaGrupoPlusRead:
    service = MateriaGrupoPlusService(db, current_user.tenant_id)
    resultado = await service.obtener(mgp_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="MateriaGrupoPlus no encontrado")
    return resultado


@router.patch(
    "/{mgp_id}",
    response_model=MateriaGrupoPlusRead,
    summary="Actualizar MateriaGrupoPlus",
)
async def actualizar_materia_grupo_plus(
    mgp_id: UUID,
    body: MateriaGrupoPlusUpdate,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MateriaGrupoPlusRead:
    service = MateriaGrupoPlusService(db, current_user.tenant_id)
    try:
        resultado = await service.actualizar(mgp_id, body, current_user)
    except VigenciaSolapadaError as e:
        raise HTTPException(status_code=409, detail={"error": "vigencia_solapada", "detalle": str(e)})
    if resultado is None:
        raise HTTPException(status_code=404, detail="MateriaGrupoPlus no encontrado")
    return resultado


@router.delete(
    "/{mgp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete MateriaGrupoPlus",
)
async def eliminar_materia_grupo_plus(
    mgp_id: UUID,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = MateriaGrupoPlusService(db, current_user.tenant_id)
    eliminado = await service.eliminar(mgp_id, current_user)
    if not eliminado:
        raise HTTPException(status_code=404, detail="MateriaGrupoPlus no encontrado")
