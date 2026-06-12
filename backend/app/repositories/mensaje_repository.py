"""Repositorio de Mensaje con queries tenant-scoped para inbox (C-20).

Reglas duras:
- Todo query filtra por tenant_id.
- Soft delete: deleted_at IS NULL por defecto.
- No accede a DB directamente desde fuera de esta capa.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mensaje import Mensaje
from app.repositories.base import BaseRepository


class MensajeRepository(BaseRepository[Mensaje]):
    """Repositorio de Mensaje con queries específicas de inbox."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, Mensaje, tenant_id)

    async def list_inbox_roots(self, user_id: UUID) -> list[Mensaje]:
        """Lista root messages (parent_id IS NULL) donde user_id es destinatario.

        Ordenados por created_at DESC (más reciente primero).
        """
        query = (
            self._base_query()
            .where(
                Mensaje.destinatario_id == user_id,
                Mensaje.parent_id.is_(None),
            )
            .order_by(Mensaje.created_at.desc())
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def get_thread(self, root_id: UUID) -> list[Mensaje]:
        """Obtiene root + replies donde parent_id == root_id.

        Ordenados por created_at ASC (cronológico).
        """
        query = (
            self._base_query()
            .where(
                (Mensaje.id == root_id) | (Mensaje.parent_id == root_id)
            )
            .order_by(Mensaje.created_at.asc())
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def get_root(self, root_id: UUID) -> Mensaje | None:
        """Obtiene un root message por ID dentro del tenant scope."""
        query = (
            self._base_query()
            .where(Mensaje.id == root_id, Mensaje.parent_id.is_(None))
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def create_reply(self, root_id: UUID, data: dict[str, Any]) -> Mensaje:
        """Crea una respuesta con parent_id = root_id.

        Hereda tenant_id del repositorio.
        """
        if "tenant_id" in data:
            raise ValueError("tenant_id must not be passed explicitly")
        data["tenant_id"] = self.tenant_id
        data["parent_id"] = root_id
        instance = Mensaje(**data)
        self.db_session.add(instance)
        await self.db_session.commit()
        await self.db_session.refresh(instance)
        return instance
