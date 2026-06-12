"""Router de facturas docentes (C-18).

Endpoints:
- POST  /api/v1/facturas                → cargar factura
- GET   /api/v1/facturas                → listar con filtros
- GET   /api/v1/facturas/{id}           → obtener por ID
- POST  /api/v1/facturas/{id}/abonar    → transición Pendiente → Abonada
- DELETE /api/v1/facturas/{id}          → soft delete
- GET   /api/v1/facturas/{id}/archivo   → descargar archivo

Permisos: fail-closed.
Identidad y tenant SIEMPRE desde JWT.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_active_user, get_db, require_permission
from app.modules.liquidaciones.exceptions import (
    FacturaYaAbonadaError,
    UsuarioNoFacturanteError,
)
from app.modules.liquidaciones.infrastructure.local_file_storage import LocalFileStorage
from app.modules.liquidaciones.schemas.factura import (
    FacturaCreate,
    FacturaListFilter,
    FacturaRead,
)
from app.modules.liquidaciones.services.factura_service import FacturaService

router = APIRouter(
    prefix="/api/v1/facturas",
    tags=["facturas"],
    responses={
        403: {"description": "Permiso denegado"},
        404: {"description": "Factura no encontrada"},
        409: {"description": "Conflicto — factura ya abonada"},
        422: {"description": "Validación fallida"},
    },
)

# Stub de storage para dev — en producción inyectar vía DI o settings
_file_storage = LocalFileStorage()


@router.post(
    "",
    response_model=FacturaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cargar factura de docente facturante",
)
async def cargar_factura(
    body: FacturaCreate,
    _perm: Annotated[object, Depends(require_permission("facturas:cargar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FacturaRead:
    """Crea una factura. Valida que usuario_id sea facturante."""
    service = FacturaService(db, current_user.tenant_id)
    try:
        return await service.cargar(body, current_user)
    except UsuarioNoFacturanteError as e:
        raise HTTPException(
            status_code=422, detail={"error": "usuario_no_es_facturante", "detalle": str(e)}
        )


@router.get(
    "",
    summary="Listar facturas con filtros",
)
async def listar_facturas(
    usuario_id: UUID | None = Query(None),
    estado: str | None = Query(None),
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _perm: Annotated[object, Depends(require_permission("facturas:ver"))] = None,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    filtros = FacturaListFilter(
        usuario_id=usuario_id,
        estado=estado,
        desde=desde,
        hasta=hasta,
        q=q,
        page=page,
        page_size=page_size,
    )
    service = FacturaService(db, current_user.tenant_id)
    items, total = await service.listar(filtros)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get(
    "/{factura_id}",
    response_model=FacturaRead,
    summary="Obtener factura por ID",
)
async def obtener_factura(
    factura_id: UUID,
    _perm: Annotated[object, Depends(require_permission("facturas:ver"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FacturaRead:
    service = FacturaService(db, current_user.tenant_id)
    resultado = await service.obtener(factura_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return resultado


@router.post(
    "/{factura_id}/abonar",
    response_model=FacturaRead,
    summary="Marcar factura como abonada",
)
async def abonar_factura(
    factura_id: UUID,
    _perm: Annotated[object, Depends(require_permission("facturas:abonar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FacturaRead:
    service = FacturaService(db, current_user.tenant_id)
    try:
        return await service.abonar(factura_id, current_user)
    except FacturaYaAbonadaError:
        raise HTTPException(status_code=409, detail={"error": "factura_ya_abonada"})
    except ValueError:
        raise HTTPException(status_code=404, detail="Factura no encontrada")


@router.delete(
    "/{factura_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete de factura",
)
async def eliminar_factura(
    factura_id: UUID,
    _perm: Annotated[object, Depends(require_permission("facturas:cargar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = FacturaService(db, current_user.tenant_id)
    eliminado = await service.eliminar(factura_id, current_user)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Factura no encontrada")


@router.get(
    "/{factura_id}/archivo",
    summary="Descargar archivo de factura",
)
async def descargar_archivo_factura(
    factura_id: UUID,
    _perm: Annotated[object, Depends(require_permission("facturas:ver"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Descarga el archivo de una factura respetando multi-tenancy (solo el propio tenant)."""
    service = FacturaService(db, current_user.tenant_id)
    factura = await service.obtener(factura_id)
    if factura is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    try:
        content = await _file_storage.download(factura.referencia_archivo)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el storage")
    return Response(content=content, media_type="application/octet-stream")
