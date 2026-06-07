"""Repository para PasswordResetToken.

Operaciones: crear, buscar por hash, marcar como usado.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update

from app.models.password_reset_token import PasswordResetToken
from app.repositories.base import BaseRepository


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    """Repositorio de tokens de recuperación de contraseña."""

    def __init__(self, db_session, tenant_id: UUID) -> None:
        super().__init__(db_session, PasswordResetToken, tenant_id)

    async def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:
        """Busca un token de reset por su hash."""
        query = self._base_query().where(PasswordResetToken.token_hash == token_hash)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def mark_used(self, token_hash: str) -> None:
        """Marca un token de reset como usado."""
        stmt = (
            update(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.tenant_id == self.tenant_id,
            )
            .values(used_at=datetime.now(timezone.utc))
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()

    async def create_reset_token(
        self,
        token_hash: str,
        user_id: UUID,
        expires_at: datetime,
    ) -> PasswordResetToken:
        """Crea un nuevo token de recuperación."""
        return await self.create(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
        )
