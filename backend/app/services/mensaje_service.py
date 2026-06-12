"""Servicio de mensajería interna (C-20).

Reglas duras:
- Thread access control: solo remitente o destinatario del root pueden leer/responder.
- Tenant-scoped: todo query filtra por tenant_id.
- Soft delete: mensajes eliminados no aparecen en inbox ni threads.
"""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction, record_audit
from app.models.mensaje import Mensaje
from app.repositories.mensaje_repository import MensajeRepository


class MensajeService:
    """Servicio de mensajería interna entre usuarios del mismo tenant."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID, actor_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self._repo = MensajeRepository(db_session, tenant_id)

    async def list_inbox(self, user_id: UUID) -> list[Mensaje]:
        """Lista threads donde el usuario es destinatario.

        Returns:
            Lista de root messages ordenados por más reciente.
        """
        return await self._repo.list_inbox_roots(user_id)

    async def get_thread(self, root_id: UUID, user_id: UUID) -> tuple[Mensaje, list[Mensaje]]:
        """Obtiene un thread (root + replies) si el usuario es participante.

        Args:
            root_id: ID del mensaje raíz.
            user_id: ID del usuario autenticado.

        Returns:
            Tupla (root_message, list_of_replies).

        Raises:
            HTTPException 403: si el usuario no es remitente ni destinatario.
            HTTPException 404: si el thread no existe.
        """
        thread = await self._repo.get_thread(root_id)
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread no encontrado",
            )

        root = next((m for m in thread if m.id == root_id and m.parent_id is None), None)
        if root is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread no encontrado",
            )

        if root.remitente_id != user_id and root.destinatario_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés acceso a este thread",
            )

        replies = [m for m in thread if m.parent_id == root_id]
        return root, replies

    async def responder(self, root_id: UUID, data: dict[str, Any]) -> Mensaje:
        """Crea una respuesta en un thread existente.

        Args:
            root_id: ID del mensaje raíz.
            data: Datos de la respuesta (asunto, cuerpo).

        Returns:
            Mensaje creado.

        Raises:
            HTTPException 403: si el actor no es participante del thread.
            HTTPException 404: si el thread no existe.
        """
        root = await self._repo.get_root(root_id)
        if root is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread no encontrado",
            )

        if root.remitente_id != self.actor_id and root.destinatario_id != self.actor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés acceso a este thread",
            )

        reply_data = {
            "remitente_id": self.actor_id,
            "destinatario_id": root.remitente_id if root.destinatario_id == self.actor_id else root.destinatario_id,
            "asunto": data.get("asunto", f"Re: {root.asunto}"),
            "cuerpo": data["cuerpo"],
        }

        reply = await self._repo.create_reply(root_id, reply_data)
        await record_audit(
            session=self.db_session,
            actor_id=self.actor_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.MENSAJE_RESPONDER,
            detalle={"mensaje_id": str(reply.id), "root_id": str(root_id)},
        )
        return reply
