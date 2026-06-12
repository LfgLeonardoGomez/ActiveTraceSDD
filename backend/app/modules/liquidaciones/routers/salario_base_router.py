"""Router de SalarioBase (C-18).

Endpoints:
- POST   /api/v1/liquidaciones/salario-base          → crear
- GET    /api/v1/liquidaciones/salario-base          → listar
- GET    /api/v1/liquidaciones/salario-base/{id}     → obtener
- PATCH  /api/v1/liquidaciones/salario-base/{id}     → actualizar
- DELETE /api/v1/liquidaciones/salario-base/{id}     → soft delete

Permiso requerido: liquidaciones:configurar-salarios
Identidad y tenant SIEMPRE desde JWT — nunca de body/path/query.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_active_user, get_db, require_permission
from app.modules.liquidaciones.exceptions import VigenciaSolapadaError
from app.modules.liquidaciones.schemas.salario_base import (
    SalarioBaseCreate,
    SalarioBaseRead,
    SalarioBaseUpdate,
)
from app.modules.liquidaciones.services.salario_base_service import SalarioBaseService

router = APIRouter(
    prefix="/api/v1/liquidaciones/salario-base",
    tags=["liquidaciones-grilla"],
    responses={
        403: {"description": "Permiso denegado"},
        409: {"description": "Vigencia solapada"},
        422: {"description": "Validación fallida"},
    },
)


@router.post(
    "",
    response_model=SalarioBaseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear entrada de SalarioBase",
)
async def crear_salario_base(
    body: SalarioBaseCreate,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioBaseRead:
    """Crea una entrada de SalarioBase para (rol, vigencia).

    tenant_id se toma EXCLUSIVAMENTE del JWT.
    """
    service = SalarioBaseService(db, current_user.tenant_id)
    try:
        return await service.crear(body, current_user)
    except VigenciaSolapadaError as e:
        raise HTTPException(status_code=409, detail={"error": "vigencia_solapada", "detalle": str(e)})


@router.get(
    "",
    response_model=list[SalarioBaseRead],
    summary="Listar SalarioBase activos",
)
async def listar_salarios_base(
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SalarioBaseRead]:
    service = SalarioBaseService(db, current_user.tenant_id)
    return await service.listar()


@router.get(
    "/{salario_id}",
    response_model=SalarioBaseRead,
    summary="Obtener SalarioBase por ID",
)
async def obtener_salario_base(
    salario_id: UUID,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioBaseRead:
    service = SalarioBaseService(db, current_user.tenant_id)
    resultado = await service.obtener(salario_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="SalarioBase no encontrado")
    return resultado


@router.patch(
    "/{salario_id}",
    response_model=SalarioBaseRead,
    summary="Actualizar SalarioBase",
)
async def actualizar_salario_base(
    salario_id: UUID,
    body: SalarioBaseUpdate,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioBaseRead:
    service = SalarioBaseService(db, current_user.tenant_id)
    try:
        resultado = await service.actualizar(salario_id, body, current_user)
    except VigenciaSolapadaError as e:
        raise HTTPException(status_code=409, detail={"error": "vigencia_solapada", "detalle": str(e)})
    if resultado is None:
        raise HTTPException(status_code=404, detail="SalarioBase no encontrado")
    return resultado


@router.delete(
    "/{salario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete SalarioBase",
)
async def eliminar_salario_base(
    salario_id: UUID,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:configurar-salarios"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = SalarioBaseService(db, current_user.tenant_id)
    eliminado = await service.eliminar(salario_id, current_user)
    if not eliminado:
        raise HTTPException(status_code=404, detail="SalarioBase no encontrado")
