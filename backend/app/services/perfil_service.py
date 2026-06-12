"""Servicio de edición de perfil propio (C-20).

Reglas duras:
- Self-service: el usuario solo puede editar su propio perfil.
- Delega a UsuarioRepository para cifrado/descifrado transparente de PII.
- No permite editar cuil (schema lo omite, pero servicio no toca ese campo).
"""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction, record_audit
from app.models.user import Usuario
from app.repositories.usuarios import UsuarioRepository


class PerfilService:
    """Servicio de edición de perfil propio del usuario autenticado."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID, actor_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self._repo = UsuarioRepository(db_session, tenant_id)

    async def editar_perfil(self, data: dict[str, Any]) -> Usuario:
        """Edita el perfil del usuario autenticado (self-service only).

        Args:
            data: Campos a actualizar (ya validados por schema).

        Returns:
            Usuario actualizado con PII descifrada.

        Raises:
            HTTPException 404: si el usuario no existe o está soft-deleted.
            HTTPException 403: si el actor intenta editar un perfil ajeno.
        """
        # Self-service guard: solo el actor puede editar su propio perfil
        usuario = await self._repo.get_by_id(self.actor_id)
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        if usuario.id != self.actor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo podés editar tu propio perfil",
            )

        updated = await self._repo.update(self.actor_id, data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        await record_audit(
            session=self.db_session,
            actor_id=self.actor_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.PERFIL_EDITAR,
            detalle={"usuario_id": str(self.actor_id)},
        )
        return updated
