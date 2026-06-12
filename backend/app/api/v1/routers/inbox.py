"""Router de mensajería interna (inbox) (C-20).

Endpoints:
- GET  /api/v1/inbox              → listar threads
- GET  /api/v1/inbox/{id}         → detalle de thread
- POST /api/v1/inbox/{id}/responder → responder en thread

Reglas duras:
- Identidad desde JWT, nunca desde URL/body.
- Guards: mensajeria:leer, mensajeria:responder.
- Thin router: valida input, delega a service, registra auditoría.
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
from app.schemas.mensajes import (
    InboxThreadDetailRead,
    InboxThreadRead,
    MensajeRead,
    MensajeReplyCreate,
)
from app.services.mensaje_service import MensajeService

router = APIRouter(
    prefix="/api/v1/inbox",
    tags=["mensajeria"],
    responses={
        403: {"description": "Permiso denegado o no sos participante"},
        404: {"description": "Thread no encontrado"},
        422: {"description": "Validación fallida"},
    },
)


@router.get(
    "",
    response_model=list[InboxThreadRead],
)
async def listar_inbox(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[None, Depends(require_permission("mensajeria:leer"))],
) -> list[InboxThreadRead]:
    """Lista threads donde el usuario autenticado es destinatario."""
    service = MensajeService(db, current_user.tenant_id, current_user.id)
    items = await service.list_inbox(current_user.id)
    return [InboxThreadRead.model_validate(m) for m in items]


@router.get(
    "/{root_id}",
    response_model=InboxThreadDetailRead,
)
async def obtener_thread(
    root_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[None, Depends(require_permission("mensajeria:leer"))],
) -> InboxThreadDetailRead:
    """Obtiene un thread (root + replies) si el usuario es participante."""
    service = MensajeService(db, current_user.tenant_id, current_user.id)
    root, replies = await service.get_thread(root_id, current_user.id)
    return InboxThreadDetailRead(
        id=root.id,
        remitente_id=root.remitente_id,
        asunto=root.asunto,
        cuerpo=root.cuerpo,
        created_at=root.created_at,
        replies=[MensajeRead.model_validate(r) for r in replies],
    )


@router.post(
    "/{root_id}/responder",
    response_model=MensajeRead,
    status_code=status.HTTP_201_CREATED,
)
async def responder_thread(
    root_id: UUID,
    body: MensajeReplyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    _perm: Annotated[None, Depends(require_permission("mensajeria:responder"))],
) -> MensajeRead:
    """Crea una respuesta en un thread existente."""
    service = MensajeService(db, current_user.tenant_id, current_user.id)
    data = body.model_dump(exclude_unset=True)
    reply = await service.responder(root_id, data)
    return MensajeRead.model_validate(reply)
