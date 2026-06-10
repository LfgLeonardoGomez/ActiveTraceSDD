"""Router de calificaciones (C-10).

Endpoints:
- POST /api/v1/calificaciones/preview          → preview sin persistir
- POST /api/v1/calificaciones/import           → confirmar importación
- POST /api/v1/calificaciones/import-finalizacion → reporte de finalización
- DELETE /api/v1/calificaciones/{materia_id}   → vaciar scope-isolated

Identidad y tenant_id provienen EXCLUSIVAMENTE del JWT verificado.
Permisos:
  calificaciones:importar → preview, import, vaciar
  calificaciones:ver      → import-finalizacion
  calificaciones:vaciar   → DELETE
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    get_current_active_user,
    get_db,
    require_permission,
)
from app.schemas.calificacion import (
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportPreviewResponse,
)
from app.services.calificacion_service import CalificacionService
from app.services.finalizacion_service import EntregaSinCorregir, FinalizacionService

_MAX_FILE_SIZE = 5 * 1024 * 1024

_common_responses = {
    403: {"description": "Permiso denegado"},
    413: {"description": "Archivo demasiado grande (máx 5 MB)"},
    422: {"description": "Validación fallida o columnas no detectadas"},
}

router = APIRouter(
    prefix="/api/v1/calificaciones",
    tags=["calificaciones"],
    responses=_common_responses,
)


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


async def _read_file(file: UploadFile) -> bytes:
    from fastapi import HTTPException  # noqa: PLC0415
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el límite de {_MAX_FILE_SIZE // (1024 * 1024)} MB",
        )
    return content


@router.post(
    "/preview",
    response_model=ImportPreviewResponse,
    summary="Vista previa de calificaciones (sin persistir)",
)
async def preview_calificaciones(
    file: UploadFile,
    _perm: Annotated[object, Depends(require_permission("calificaciones:importar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImportPreviewResponse:
    """Parsea el archivo y devuelve actividades detectadas sin persistir."""
    content = await _read_file(file)
    service = CalificacionService(db, current_user.tenant_id)
    return await service.preview_import(content, file.filename or "upload.csv")


@router.post(
    "/import",
    response_model=ImportConfirmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirmar importación de calificaciones",
)
async def import_calificaciones(
    file: UploadFile,
    body: ImportConfirmRequest = Depends(),
    _perm: object = Depends(require_permission("calificaciones:importar")),
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> ImportConfirmResponse:
    """Persiste las calificaciones de las actividades seleccionadas."""
    content = await _read_file(file)
    service = CalificacionService(db, current_user.tenant_id)
    return await service.confirm_import(
        file_bytes=content,
        filename=file.filename or "upload.csv",
        materia_id=body.materia_id,
        actividades_seleccionadas=body.actividades_seleccionadas,
        current_user=current_user,
        ip=_get_client_ip(request) if request else None,
    )


@router.post(
    "/import-finalizacion",
    response_model=list[EntregaSinCorregir],
    summary="Detectar entregas sin calificar (reporte de finalización)",
)
async def import_finalizacion(
    file: UploadFile,
    materia_id: UUID,
    _perm: Annotated[object, Depends(require_permission("calificaciones:ver"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[EntregaSinCorregir]:
    """Cruza el reporte de finalización con las calificaciones y devuelve posibles entregas sin corregir."""
    content = await _read_file(file)
    service = FinalizacionService(db, current_user.tenant_id)
    return await service.detectar_sin_corregir(
        file_bytes=content,
        filename=file.filename or "upload.csv",
        materia_id=materia_id,
        current_user=current_user,
    )


@router.delete(
    "/{materia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Vaciar calificaciones de una materia (scope-isolated, RN-04)",
)
async def vaciar_calificaciones(
    materia_id: UUID,
    _perm: Annotated[object, Depends(require_permission("calificaciones:vaciar"))],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request = None,
) -> None:
    """Soft delete de las calificaciones del docente autenticado en la materia."""
    service = CalificacionService(db, current_user.tenant_id)
    await service.vaciar_materia(
        materia_id=materia_id,
        current_user=current_user,
        ip=_get_client_ip(request) if request else None,
    )
