"""Repositorio de Usuario con cifrado transparente de PII (C-07).

Cifrado/descifrado de PII ocurre SOLO en esta capa:
- Al escribir: _encrypt_pii_fields(data) cifra antes de persistir.
- Al leer: _decrypt_pii_instance(instance) descifra después de leer.
- El service trabaja SIEMPRE con texto plano.
- PII fields: email, dni, cuil, cbu, alias_cbu.

D-01: Cifrado transparente en repositorio.
D-02: email_hash para lookup determinístico.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_pii, encrypt_pii, hash_email_for_lookup
from app.models.user import Usuario
from app.repositories.base import BaseRepository

# Campos PII que se cifran al escribir y se descifran al leer
_PII_FIELDS = ("email", "dni", "cuil", "cbu", "alias_cbu")


class UsuarioRepository(BaseRepository[Usuario]):
    """Repositorio de Usuario con cifrado transparente de PII.

    Todo método de lectura devuelve instancias con PII descifrada.
    Todo método de escritura cifra PII antes de persistir.
    """

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, Usuario, tenant_id)

    # ------------------------------------------------------------------
    # Helpers privados de cifrado
    # ------------------------------------------------------------------

    def _encrypt_pii_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """Cifra campos PII en el dict de datos antes de persistir.

        - Cifra cada campo PII presente en data.
        - Si se incluye 'email', calcula automáticamente email_hash.
        - No modifica campos no-PII.

        Returns:
            Nuevo dict con campos PII cifrados.
        """
        result = dict(data)
        for field in _PII_FIELDS:
            if field in result and result[field] is not None:
                result[field] = encrypt_pii(str(result[field]))
        # Calcular email_hash si el email está presente
        if "email" in data and data["email"] is not None:
            result["email_hash"] = hash_email_for_lookup(str(data["email"]))
        return result

    def _decrypt_pii_instance(self, instance: Usuario) -> Usuario:
        """Descifra PII de una instancia Usuario in-place.

        Reemplaza los ciphertexts de campos PII con texto plano.
        Opera in-place para no crear instancias huérfanas.

        Returns:
            La misma instancia con PII descifrada.
        """
        for field in _PII_FIELDS:
            value = getattr(instance, field, None)
            if value is not None:
                try:
                    setattr(instance, field, decrypt_pii(value))
                except Exception:
                    # Si falla el descifrado (campo no era ciphertext), dejar intacto
                    pass
        return instance

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    async def create(self, **kwargs: Any) -> Usuario:
        """Crea usuario cifrando PII y calculando email_hash.

        Raises:
            IntegrityError: si viola el índice único (tenant_id, email_hash).
        """
        if "tenant_id" in kwargs:
            raise ValueError("tenant_id must not be passed explicitly")
        encrypted = self._encrypt_pii_fields(kwargs)
        encrypted["tenant_id"] = self.tenant_id

        instance = Usuario(**encrypted)
        self.db_session.add(instance)
        await self.db_session.commit()
        await self.db_session.refresh(instance)
        return self._decrypt_pii_instance(instance)

    async def get_by_id(self, obj_id: UUID) -> Usuario | None:
        """Busca usuario por ID dentro del tenant scope. Descifra PII."""
        query = self._base_query().where(Usuario.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        return self._decrypt_pii_instance(instance)

    async def get_by_email_hash(self, email: str) -> Usuario | None:
        """Busca usuario por email (lookup vía HMAC-SHA256).

        Calcula el hash del email y lo busca en la columna email_hash.
        Solo retorna usuarios activos (no soft-deleted) del tenant.

        Args:
            email: Email en texto plano (se hashea internamente).

        Returns:
            Usuario con PII descifrada, o None si no existe.
        """
        email_hash = hash_email_for_lookup(email)
        query = self._base_query().where(Usuario.email_hash == email_hash)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        return self._decrypt_pii_instance(instance)

    async def exists_by_email_hash(
        self, email: str, exclude_id: UUID | None = None
    ) -> bool:
        """Verifica si existe un usuario activo con el email en el tenant.

        Args:
            email: Email en texto plano.
            exclude_id: ID a excluir (para updates — no contar el propio registro).

        Returns:
            True si existe otro usuario activo con el mismo email.
        """
        email_hash = hash_email_for_lookup(email)
        query = self._base_query().where(Usuario.email_hash == email_hash)
        if exclude_id is not None:
            query = query.where(Usuario.id != exclude_id)
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db_session.execute(count_query)
        return result.scalar_one() > 0

    async def list_paginated(
        self,
        limit: int = 50,
        offset: int = 0,
        estado: str | None = None,
    ) -> tuple[list[Usuario], int]:
        """Lista usuarios paginados del tenant con PII descifrada.

        Returns:
            Tuple (items_descifrados, total_count).
        """
        base = self._base_query()
        if estado is not None:
            base = base.where(Usuario.estado == estado)

        count_query = select(func.count()).select_from(base.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = base.limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.scalars().all())

        return [self._decrypt_pii_instance(u) for u in items], total

    async def update(self, obj_id: UUID, data: dict[str, Any]) -> Usuario | None:
        """Actualiza usuario re-cifrando PII si cambia.

        Si el email cambia, recalcula email_hash automáticamente.

        Returns:
            Usuario actualizado con PII descifrada, o None si no encontrado.
        """
        query = self._base_query().where(Usuario.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None

        encrypted_data = self._encrypt_pii_fields(data)
        for key, value in encrypted_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        instance.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(instance)
        return self._decrypt_pii_instance(instance)

    async def soft_delete(self, obj_id: UUID) -> bool:
        """Soft delete: setea deleted_at en lugar de borrar físicamente.

        Returns:
            True si el registro fue encontrado y marcado como eliminado.
        """
        query = self._base_query().where(Usuario.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return False

        instance.deleted_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        return True
