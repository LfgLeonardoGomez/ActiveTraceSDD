"""Router de SalarioPlus (C-18).

Endpoints:
- POST   /api/v1/liquidaciones/salario-plus          → crear
- GET    /api/v1/liquidaciones/salario-plus          → listar
- GET    /api/v1/liquidaciones/salario-plus/{id}     → obtener
- PATCH  /api/v1/liquidaciones/salario-plus/{id}     → actualizar
- DELETE /api/v1/liquidaciones/salario-plus/{id}     → soft delete

Permiso requerido: liquidaciones:configurar-salarios
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_active_user, get_db, require_permission
from app.modules.liquidaciones.exceptions import VigenciaSolapadaError
from app.modules.liquidaciones.schemas.salario_plus import (
    SalarioPlusCreate,
    SalarioPlusRead,
    SalarioPlusUpdate,
)
from app.modules.liquidaciones.services.salario_plus_service import SalarioPlusService

router = APIRouter(
    prefix="/api/v1/liquidaciones/salario-plus",
    tags=["liquidaciones-grilla"],
    responses={
        403: {"description": "Permiso denegado"},
        409: {"description": "Vigencia solapada"},
        422: {"description": "Validación fallida"},
    },
)


@router.post(
    "",
    response_model=SalarioPlusRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear entrada de SalarioPlus",
)
async def crear_salario_plus(
    body: SalarioPlusCreate,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioPlusRead:
    service = SalarioPlusService(db, current_user.tenant_id)
    try:
        return await service.crear(body, current_user)
    except VigenciaSolapadaError as e:
        raise HTTPException(status_code=409, detail={"error": "vigencia_solapada", "detalle": str(e)})


@router.get(
    "",
    response_model=list[SalarioPlusRead],
    summary="Listar SalarioPlus activos",
)
async def listar_salarios_plus(
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SalarioPlusRead]:
    service = SalarioPlusService(db, current_user.tenant_id)
    return await service.listar()


@router.get(
    "/{plus_id}",
    response_model=SalarioPlusRead,
    summary="Obtener SalarioPlus por ID",
)
async def obtener_salario_plus(
    plus_id: UUID,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioPlusRead:
    service = SalarioPlusService(db, current_user.tenant_id)
    resultado = await service.obtener(plus_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="SalarioPlus no encontrado")
    return resultado


@router.patch(
    "/{plus_id}",
    response_model=SalarioPlusRead,
    summary="Actualizar SalarioPlus",
)
async def actualizar_salario_plus(
    plus_id: UUID,
    body: SalarioPlusUpdate,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioPlusRead:
    service = SalarioPlusService(db, current_user.tenant_id)
    try:
        resultado = await service.actualizar(plus_id, body, current_user)
    except VigenciaSolapadaError as e:
        raise HTTPException(status_code=409, detail={"error": "vigencia_solapada", "detalle": str(e)})
    if resultado is None:
        raise HTTPException(status_code=404, detail="SalarioPlus no encontrado")
    return resultado


@router.delete(
    "/{plus_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete SalarioPlus",
)
async def eliminar_salario_plus(
    plus_id: UUID,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = SalarioPlusService(db, current_user.tenant_id)
    eliminado = await service.eliminar(plus_id, current_user)
    if not eliminado:
        raise HTTPException(status_code=404, detail="SalarioPlus no encontrado")
