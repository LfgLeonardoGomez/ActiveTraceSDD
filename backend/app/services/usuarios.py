"""Servicio de gestión de usuarios con PII cifrada (C-07).

Reglas de negocio:
- Unicidad email por tenant (409 semántico antes de insertar)
- PII nunca expuesta en mensajes de error
- Soft delete (nunca borrado físico)
- Re-verificar unicidad al cambiar email en update

No accede directamente a DB: delega todo al UsuarioRepository.
"""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Usuario
from app.repositories.usuarios import UsuarioRepository


class UsuarioService:
    """Servicio de gestión de usuarios del tenant."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._repo = UsuarioRepository(db_session, tenant_id)

    async def crear_usuario(
        self,
        nombre: str,
        apellidos: str,
        email: str,
        estado: str,
        **kwargs: Any,
    ) -> Usuario:
        """Crea un usuario en el tenant.

        Verifica unicidad de email (409 semántico si ya existe).
        El mensaje de error NO contiene el email en texto plano.

        Returns:
            Usuario creado con PII descifrada.

        Raises:
            HTTPException 409: si el email ya existe en el tenant.
        """
        if await self._repo.exists_by_email_hash(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario activo con ese email en el tenant",
            )

        return await self._repo.create(
            nombre=nombre,
            apellidos=apellidos,
            email=email,
            estado=estado,
            **kwargs,
        )

    async def listar_usuarios(
        self,
        limit: int = 50,
        offset: int = 0,
        estado: str | None = None,
    ) -> tuple[list[Usuario], int]:
        """Lista usuarios del tenant con paginación.

        Returns:
            Tuple (items_descifrados, total).
        """
        return await self._repo.list_paginated(
            limit=limit, offset=offset, estado=estado
        )

    async def obtener_usuario(self, usuario_id: UUID) -> Usuario:
        """Obtiene un usuario por ID dentro del tenant.

        Returns:
            Usuario con PII descifrada.

        Raises:
            HTTPException 404: si no existe en el tenant.
        """
        usuario = await self._repo.get_by_id(usuario_id)
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        return usuario

    async def actualizar_usuario(
        self, usuario_id: UUID, data: dict[str, Any]
    ) -> Usuario:
        """Actualiza campos de un usuario (parcial).

        Si el email cambia, re-verifica unicidad (409 si ya existe).
        El repositorio re-cifra PII automáticamente.

        Returns:
            Usuario actualizado con PII descifrada.

        Raises:
            HTTPException 404: si no existe.
            HTTPException 409: si el nuevo email ya existe en el tenant.
        """
        # Verificar existencia
        await self.obtener_usuario(usuario_id)

        # Re-verificar unicidad si el email cambia
        if "email" in data and data["email"] is not None:
            if await self._repo.exists_by_email_hash(data["email"], exclude_id=usuario_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe un usuario activo con ese email en el tenant",
                )

        updated = await self._repo.update(usuario_id, data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        return updated

    async def desactivar_usuario(self, usuario_id: UUID) -> Usuario:
        """Desactiva un usuario (cambia estado a Inactivo).

        Returns:
            Usuario actualizado.
        """
        return await self.actualizar_usuario(usuario_id, {"estado": "Inactivo"})

    async def eliminar_usuario(self, usuario_id: UUID) -> bool:
        """Soft delete de usuario (setea deleted_at).

        Returns:
            True si fue encontrado y eliminado.

        Raises:
            HTTPException 404: si no existe.
        """
        result = await self._repo.soft_delete(usuario_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )
        return True
