"""Router del padrón de alumnos (C-09).

Todos los endpoints requieren permiso `padron:cargar`.
PROFESOR: scope propio (is_propio=True) — solo sus materias asignadas.
COORDINADOR: scope global (is_propio=False) — cualquier materia del tenant.

Identidad y tenant_id provienen EXCLUSIVAMENTE del JWT verificado.

Endpoints:
- POST /api/v1/padron/preview         → parsea y retorna preview sin persistir
- POST /api/v1/padron/confirm         → confirma importación y activa versión
- DELETE /api/v1/padron/{materia_id}  → vacía padrón (scope-isolated)
- POST /api/v1/padron/moodle-sync     → sync on-demand con Moodle WS
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    get_current_active_user,
    get_db,
    require_permission,
)
from app.schemas.padron import (
    MoodleSyncRequest,
    PadronConfirmResponse,
    PadronPreviewResponse,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.padron_service import PadronService

# Límite de tamaño de archivo: 5 MB
_MAX_FILE_SIZE = 5 * 1024 * 1024  # bytes

_common_responses = {
    403: {"description": "Permiso denegado"},
    413: {"description": "Archivo demasiado grande (máx 5 MB)"},
    422: {"description": "Validación fallida o columnas faltantes"},
}

router = APIRouter(
    prefix="/api/v1/padron",
    tags=["padron"],
    responses=_common_responses,
)


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


async def _read_and_validate_file(file: UploadFile) -> bytes:
    """Lee y valida el tamaño del archivo subido."""
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el límite de {_MAX_FILE_SIZE // (1024*1024)} MB",
        )
    return content


def _validate_materia_scope(
    perm: PermissionContext,
    current_user: CurrentUser,
    materia_asignada_al_usuario: bool,
) -> None:
    """Valida scope para PROFESOR (is_propio=True).

    Si el permiso es propio, el usuario solo puede operar sobre materias
    que le están asignadas.
    """
    if perm.is_propio and not materia_asignada_al_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permiso para operar sobre esta materia",
        )


@router.post(
    "/preview",
    response_model=PadronPreviewResponse,
    status_code=status.HTTP_200_OK,
)
async def preview_padron(
    file: UploadFile,
    materia_id: UUID,
    cohorte_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm: Annotated[PermissionContext, Depends(require_permission("padron:cargar"))],
) -> PadronPreviewResponse:
    """Parsea el archivo y retorna un preview sin persistir nada.

    Valida el scope: PROFESOR solo puede operar sus propias materias.
    """
    content = await _read_and_validate_file(file)

    if perm.is_propio:
        from app.repositories.asignaciones import AsignacionRepository
        asig_repo = AsignacionRepository(db, current_user.tenant_id)
        tiene_asignacion = await asig_repo.exists_active_for_user_and_materia(
            usuario_id=current_user.id,
            materia_id=materia_id,
        )
        _validate_materia_scope(perm, current_user, tiene_asignacion)

    rows, errors = PadronService.parse_file(content, file.filename or "padron.csv")
    return PadronService.generate_preview(rows, errors)


@router.post(
    "/confirm",
    response_model=PadronConfirmResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_padron(
    file: UploadFile,
    materia_id: UUID,
    cohorte_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm: Annotated[PermissionContext, Depends(require_permission("padron:cargar"))],
) -> PadronConfirmResponse:
    """Importa el padrón: parsea, persiste y activa la nueva versión."""
    content = await _read_and_validate_file(file)

    if perm.is_propio:
        from app.repositories.asignaciones import AsignacionRepository
        asig_repo = AsignacionRepository(db, current_user.tenant_id)
        tiene_asignacion = await asig_repo.exists_active_for_user_and_materia(
            usuario_id=current_user.id,
            materia_id=materia_id,
        )
        _validate_materia_scope(perm, current_user, tiene_asignacion)

    rows, _errors = PadronService.parse_file(content, file.filename or "padron.csv")

    svc = PadronService(db, current_user.tenant_id)
    version = await svc.confirm_import(
        rows=rows,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        cargado_por_id=current_user.real_actor_id,
        ip=_get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    return PadronConfirmResponse(
        version_id=version.id,
        materia_id=version.materia_id,
        cohorte_id=version.cohorte_id,
        filas_importadas=len(rows),
        activa=version.activa,
        origen=version.origen,
    )


@router.delete(
    "/{materia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def vaciar_padron(
    materia_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm: Annotated[PermissionContext, Depends(require_permission("padron:cargar"))],
) -> None:
    """Vacía el padrón de una materia (scope-isolated, RN-04)."""
    if perm.is_propio:
        from app.repositories.asignaciones import AsignacionRepository
        asig_repo = AsignacionRepository(db, current_user.tenant_id)
        tiene_asignacion = await asig_repo.exists_active_for_user_and_materia(
            usuario_id=current_user.id,
            materia_id=materia_id,
        )
        _validate_materia_scope(perm, current_user, tiene_asignacion)

    svc = PadronService(db, current_user.tenant_id)
    await svc.vaciar_padron(
        materia_id=materia_id,
        cargado_por_id=current_user.real_actor_id,
        ip=_get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.post(
    "/moodle-sync",
    response_model=PadronConfirmResponse,
    status_code=status.HTTP_200_OK,
)
async def moodle_sync(
    body: MoodleSyncRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    perm: Annotated[PermissionContext, Depends(require_permission("padron:cargar"))],
) -> PadronConfirmResponse:
    """Sincroniza el padrón desde Moodle WS (on-demand)."""
    from app.integrations.moodle_ws import MoodleWSClient, MoodleNotConfiguredError, MoodleWSError
    from app.core.config import Settings

    settings = Settings()
    if not settings.moodle_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "MOODLE_NOT_CONFIGURED"},
        )

    if perm.is_propio:
        from app.repositories.asignaciones import AsignacionRepository
        asig_repo = AsignacionRepository(db, current_user.tenant_id)
        tiene_asignacion = await asig_repo.exists_active_for_user_and_materia(
            usuario_id=current_user.id,
            materia_id=body.materia_id,
        )
        _validate_materia_scope(perm, current_user, tiene_asignacion)

    try:
        client = MoodleWSClient(settings.moodle_url, settings.moodle_token or "")
        moodle_rows = await client.get_padron_rows(body.course_id)
    except MoodleNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "MOODLE_NOT_CONFIGURED"},
        )
    except MoodleWSError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "MOODLE_WS_ERROR", "retry_after": exc.retry_after},
        )

    svc = PadronService(db, current_user.tenant_id)
    version = await svc.confirm_import(
        rows=moodle_rows,
        materia_id=body.materia_id,
        cohorte_id=body.cohorte_id,
        cargado_por_id=current_user.real_actor_id,
        origen="moodle_ws",
        ip=_get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    return PadronConfirmResponse(
        version_id=version.id,
        materia_id=version.materia_id,
        cohorte_id=version.cohorte_id,
        filas_importadas=len(moodle_rows),
        activa=version.activa,
        origen=version.origen,
    )
