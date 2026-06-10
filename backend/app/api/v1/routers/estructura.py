"""Routers de estructura académica (C-06): Carreras, Cohortes, Materias.

Todos protegidos por require_permission("estructura:gestionar") — solo ADMIN.
Identidad y tenant_id provienen EXCLUSIVAMENTE del JWT verificado.
Fail-closed: sin permiso → 403 (sin excepciones).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_active_user, get_db, require_permission
from app.schemas.rbac_schema import PermissionContext
from app.schemas.estructura import (
    CarreraCreate,
    CarreraRead,
    CarreraUpdate,
    CohorteCreate,
    CohorteRead,
    CohorteUpdate,
    MateriaCreate,
    MateriaRead,
    MateriaUpdate,
    PaginatedCarrerasResponse,
    PaginatedCohortesResponse,
    PaginatedMateriasResponse,
)
from app.services.estructura import CarreraService, CohorteService, MateriaService

_common_responses = {
    403: {"description": "Permiso denegado"},
    404: {"description": "Recurso no encontrado"},
    409: {"description": "Conflicto de unicidad o regla de negocio"},
    422: {"description": "Validación fallida"},
}

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["estructura-academica"],
    responses=_common_responses,
)


# ================================================================
# Carreras
# ================================================================


@router.post(
    "/carreras",
    response_model=CarreraRead,
    status_code=status.HTTP_201_CREATED,
)
async def crear_carrera(
    body: CarreraCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> CarreraRead:
    """Crea una carrera nueva en el tenant del actor autenticado."""
    service = CarreraService(db, current_user.tenant_id)
    carrera = await service.crear_carrera(
        codigo=body.codigo,
        nombre=body.nombre,
        estado=body.estado,
    )
    return CarreraRead.model_validate(carrera)


@router.get(
    "/carreras",
    response_model=PaginatedCarrerasResponse,
)
async def listar_carreras(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    estado: Annotated[str | None, Query()] = None,
) -> PaginatedCarrerasResponse:
    """Lista carreras del tenant con paginación y filtro opcional por estado."""
    service = CarreraService(db, current_user.tenant_id)
    items, total = await service.listar_carreras(limit=limit, offset=offset, estado=estado)
    return PaginatedCarrerasResponse(
        items=[CarreraRead.model_validate(c) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/carreras/{carrera_id}",
    response_model=CarreraRead,
)
async def obtener_carrera(
    carrera_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> CarreraRead:
    """Obtiene detalle de una carrera por ID."""
    service = CarreraService(db, current_user.tenant_id)
    carrera = await service.obtener_carrera(carrera_id)
    return CarreraRead.model_validate(carrera)


@router.put(
    "/carreras/{carrera_id}",
    response_model=CarreraRead,
)
async def actualizar_carrera(
    carrera_id: UUID,
    body: CarreraUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> CarreraRead:
    """Actualiza campos de una carrera (parcial — solo los enviados)."""
    service = CarreraService(db, current_user.tenant_id)
    data = body.model_dump(exclude_unset=True)
    carrera = await service.actualizar_carrera(carrera_id, data)
    return CarreraRead.model_validate(carrera)


@router.delete(
    "/carreras/{carrera_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def eliminar_carrera(
    carrera_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> None:
    """Soft delete de carrera (setea deleted_at)."""
    service = CarreraService(db, current_user.tenant_id)
    await service.eliminar_carrera(carrera_id)


# ================================================================
# Cohortes
# ================================================================


@router.post(
    "/cohortes",
    response_model=CohorteRead,
    status_code=status.HTTP_201_CREATED,
)
async def crear_cohorte(
    body: CohorteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> CohorteRead:
    """Crea una cohorte bajo una carrera activa del tenant."""
    service = CohorteService(db, current_user.tenant_id)
    cohorte = await service.crear_cohorte(
        carrera_id=body.carrera_id,
        nombre=body.nombre,
        anio=body.anio,
        vig_desde=body.vig_desde,
        vig_hasta=body.vig_hasta,
        estado=body.estado,
    )
    return CohorteRead.model_validate(cohorte)


@router.get(
    "/cohortes",
    response_model=PaginatedCohortesResponse,
)
async def listar_cohortes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    estado: Annotated[str | None, Query()] = None,
    carrera_id: Annotated[UUID | None, Query()] = None,
) -> PaginatedCohortesResponse:
    """Lista cohortes del tenant con paginación y filtros opcionales."""
    service = CohorteService(db, current_user.tenant_id)
    items, total = await service.listar_cohortes(
        limit=limit, offset=offset, estado=estado, carrera_id=carrera_id
    )
    return PaginatedCohortesResponse(
        items=[CohorteRead.model_validate(c) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/cohortes/{cohorte_id}",
    response_model=CohorteRead,
)
async def obtener_cohorte(
    cohorte_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> CohorteRead:
    """Obtiene detalle de una cohorte por ID."""
    service = CohorteService(db, current_user.tenant_id)
    cohorte = await service.obtener_cohorte(cohorte_id)
    return CohorteRead.model_validate(cohorte)


@router.put(
    "/cohortes/{cohorte_id}",
    response_model=CohorteRead,
)
async def actualizar_cohorte(
    cohorte_id: UUID,
    body: CohorteUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> CohorteRead:
    """Actualiza campos de una cohorte (parcial)."""
    service = CohorteService(db, current_user.tenant_id)
    data = body.model_dump(exclude_unset=True)
    cohorte = await service.actualizar_cohorte(cohorte_id, data)
    return CohorteRead.model_validate(cohorte)


@router.delete(
    "/cohortes/{cohorte_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def eliminar_cohorte(
    cohorte_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> None:
    """Soft delete de cohorte."""
    service = CohorteService(db, current_user.tenant_id)
    await service.eliminar_cohorte(cohorte_id)


# ================================================================
# Materias
# ================================================================


@router.post(
    "/materias",
    response_model=MateriaRead,
    status_code=status.HTTP_201_CREATED,
)
async def crear_materia(
    body: MateriaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> MateriaRead:
    """Crea una materia nueva en el tenant del actor autenticado."""
    service = MateriaService(db, current_user.tenant_id)
    materia = await service.crear_materia(
        codigo=body.codigo,
        nombre=body.nombre,
        estado=body.estado,
    )
    return MateriaRead.model_validate(materia)


@router.get(
    "/materias",
    response_model=PaginatedMateriasResponse,
)
async def listar_materias(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    estado: Annotated[str | None, Query()] = None,
) -> PaginatedMateriasResponse:
    """Lista materias del tenant con paginación y filtro opcional por estado."""
    service = MateriaService(db, current_user.tenant_id)
    items, total = await service.listar_materias(limit=limit, offset=offset, estado=estado)
    return PaginatedMateriasResponse(
        items=[MateriaRead.model_validate(m) for m in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/materias/{materia_id}",
    response_model=MateriaRead,
)
async def obtener_materia(
    materia_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> MateriaRead:
    """Obtiene detalle de una materia por ID."""
    service = MateriaService(db, current_user.tenant_id)
    materia = await service.obtener_materia(materia_id)
    return MateriaRead.model_validate(materia)


@router.put(
    "/materias/{materia_id}",
    response_model=MateriaRead,
)
async def actualizar_materia(
    materia_id: UUID,
    body: MateriaUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> MateriaRead:
    """Actualiza campos de una materia (parcial)."""
    service = MateriaService(db, current_user.tenant_id)
    data = body.model_dump(exclude_unset=True)
    materia = await service.actualizar_materia(materia_id, data)
    return MateriaRead.model_validate(materia)


@router.delete(
    "/materias/{materia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def eliminar_materia(
    materia_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[PermissionContext, Depends(require_permission("estructura:gestionar"))],
) -> None:
    """Soft delete de materia."""
    service = MateriaService(db, current_user.tenant_id)
    await service.eliminar_materia(materia_id)
