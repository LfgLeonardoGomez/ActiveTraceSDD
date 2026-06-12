"""Router de liquidaciones (C-18).

Endpoints:
- GET  /api/v1/liquidaciones/{cohorte_id}/{periodo}          → calcular/ver
- GET  /api/v1/liquidaciones/{cohorte_id}/{periodo}/exportar → exportar JSON
- POST /api/v1/liquidaciones/{cohorte_id}/{periodo}/cerrar   → cierre inmutable
- GET  /api/v1/liquidaciones/historial                       → historial paginado

Permisos: fail-closed con require_permission.
Identidad y tenant SIEMPRE desde JWT — NUNCA de body/path/query.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_active_user, get_db, require_permission
from app.modules.liquidaciones.exceptions import PeriodoYaCerradoError
from app.modules.liquidaciones.schemas.liquidacion import (
    CerrarLiquidacionRequest,
    HistorialResponse,
    LiquidacionPeriodoResponse,
)
from app.modules.liquidaciones.services.historial_service import HistorialService
from app.modules.liquidaciones.services.liquidacion_calc_service import LiquidacionCalcService
from app.modules.liquidaciones.services.liquidacion_cierre_service import LiquidacionCierreService

router = APIRouter(
    prefix="/api/v1/liquidaciones",
    tags=["liquidaciones"],
    responses={
        403: {"description": "Permiso denegado"},
        404: {"description": "Recurso no encontrado"},
        409: {"description": "Conflicto — período ya cerrado o liquidación inmutable"},
        422: {"description": "Validación fallida"},
    },
)


@router.get(
    "/historial",
    response_model=HistorialResponse,
    summary="Historial paginado de liquidaciones cerradas",
)
async def listar_historial(
    cohorte_id: UUID | None = Query(None),
    usuario_id: UUID | None = Query(None),
    desde: str | None = Query(None, description="Período inicio AAAA-MM"),
    hasta: str | None = Query(None, description="Período fin AAAA-MM"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _perm: Annotated[object, Depends(require_permission("liquidaciones:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> HistorialResponse:
    service = HistorialService(db, current_user.tenant_id)
    return await service.listar_historial(
        cohorte_id=cohorte_id,
        usuario_id=usuario_id,
        desde_periodo=desde,
        hasta_periodo=hasta,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{cohorte_id}/{periodo}",
    response_model=LiquidacionPeriodoResponse,
    summary="Calcular o ver liquidación del período",
)
async def ver_liquidacion(
    cohorte_id: UUID,
    periodo: str,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:ver"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LiquidacionPeriodoResponse:
    """Retorna la liquidación del período.

    - Si cerrado: snapshot persistido (no recalcula).
    - Si abierto: cálculo on-demand con la grilla vigente.
    """
    service = LiquidacionCalcService(db, current_user.tenant_id)
    return await service.calcular_periodo(cohorte_id, periodo, current_user)


@router.get(
    "/{cohorte_id}/{periodo}/exportar",
    response_model=LiquidacionPeriodoResponse,
    summary="Exportar liquidación del período (JSON serializable)",
)
async def exportar_liquidacion(
    cohorte_id: UUID,
    periodo: str,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:exportar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LiquidacionPeriodoResponse:
    """Misma respuesta que ver_liquidacion pero con permiso exportar."""
    service = LiquidacionCalcService(db, current_user.tenant_id)
    return await service.calcular_periodo(cohorte_id, periodo, current_user)


@router.post(
    "/{cohorte_id}/{periodo}/cerrar",
    response_model=LiquidacionPeriodoResponse,
    summary="Cerrar inmutablemente el período",
)
async def cerrar_liquidacion(
    cohorte_id: UUID,
    periodo: str,
    body: CerrarLiquidacionRequest,
    _perm: Annotated[object, Depends(require_permission("liquidaciones:cerrar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LiquidacionPeriodoResponse:
    """Cierra el período.

    Validaciones previas al service:
    - confirmar_cierre debe ser true (validado por Pydantic).
    - periodo del body debe coincidir con el de la URL (TOCTOU).
    """
    # Defensa TOCTOU
    if body.periodo != periodo:
        raise HTTPException(
            status_code=400,
            detail={"error": "periodo_mismatch"},
        )

    service = LiquidacionCierreService(db, current_user.tenant_id)
    try:
        return await service.cerrar_periodo(cohorte_id, periodo, current_user)
    except PeriodoYaCerradoError:
        raise HTTPException(
            status_code=409,
            detail={"error": "periodo_ya_cerrado"},
        )
