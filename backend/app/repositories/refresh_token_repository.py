"""Repository para RefreshToken con scope de tenant.

Operaciones especializadas: búsqueda por hash, marcado como usado,
revocación masiva por usuario.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repositorio de tokens de refresco."""

    def __init__(self, db_session, tenant_id: UUID) -> None:
        super().__init__(db_session, RefreshToken, tenant_id)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Busca un refresh token por su hash (SHA-256)."""
        query = self._base_query().where(RefreshToken.token_hash == token_hash)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def mark_used(self, token_hash: str) -> None:
        """Marca un refresh token como usado."""
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.tenant_id == self.tenant_id,
            )
            .values(used_at=datetime.now(timezone.utc))
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revoca todos los refresh tokens vigentes de un usuario."""
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.tenant_id == self.tenant_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.deleted_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()

    async def create_refresh_token(
        self,
        token_hash: str,
        user_id: UUID,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> RefreshToken:
        """Crea un nuevo refresh token."""
        return await self.create(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
