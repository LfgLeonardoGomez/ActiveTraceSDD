"""Servicio de gestión de tokens: emisión, rotación, revocación.

Opera sobre RefreshTokenRepository. No accede directamente a DB.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core import security
from app.core.config import Settings
from app.models.user import Usuario
from app.repositories.refresh_token_repository import RefreshTokenRepository

settings = Settings()


class TokenService:
    """Servicio de emisión y rotación de tokens JWT + refresh."""

    def __init__(self, refresh_token_repo: RefreshTokenRepository) -> None:
        self.refresh_token_repo = refresh_token_repo

    async def issue_token_pair(
        self,
        user: Usuario,
        ip_address: str | None,
        user_agent: str | None,
        roles: list[str] | None = None,
    ) -> tuple[str, str]:
        """Emite un par access + refresh token.

        Returns:
            (access_token, raw_refresh_token)
        """
        if roles is None:
            roles = []

        access_token = security.create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            roles=roles,
        )
        raw_refresh = security.create_refresh_token()
        refresh_hash = security.hash_refresh_token(raw_refresh)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )

        await self.refresh_token_repo.create_refresh_token(
            token_hash=refresh_hash,
            user_id=user.id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return access_token, raw_refresh

    async def rotate_refresh_token(
        self,
        raw_refresh: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[str, str]:
        """Rota un refresh token: valida, invalida anterior, emite nuevo par.

        Detección de reuse: si el token ya tiene used_at → revoca todos los
        refresh tokens del usuario y lanza 401.

        Returns:
            (new_access_token, new_raw_refresh_token)

        Raises:
            AuthenticationError: si el token es inválido, expirado o reusado.
        """
        refresh_hash = security.hash_refresh_token(raw_refresh)
        token = await self.refresh_token_repo.get_by_token_hash(refresh_hash)

        if token is None:
            raise AuthenticationError("Invalid refresh token")

        if token.used_at is not None:
            # Reuse detectado: revocar toda la familia
            await self.refresh_token_repo.revoke_all_for_user(token.user_id)
            raise AuthenticationError("Refresh token reused")

        if token.revoked_at is not None:
            raise AuthenticationError("Refresh token revoked")

        if token.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Refresh token expired")

        # Marcar como usado
        await self.refresh_token_repo.mark_used(refresh_hash)

        # Obtener usuario para emitir nuevo par (sin cargar relaciones de roles aún)
        # Nota: en C-04 se resolverán roles reales; por ahora lista vacía.
        # Para evitar importación circular, usamos el repositorio base o raw query.
        # Aquí asumimos que el caller provee el usuario o lo buscamos vía session.
        from sqlalchemy import select
        from app.models.user import Usuario
        result = await self.refresh_token_repo.db_session.execute(
            select(Usuario).where(
                Usuario.id == token.user_id,
                Usuario.tenant_id == token.tenant_id,
                Usuario.deleted_at.is_(None),
            )
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise AuthenticationError("User not found")

        return await self.issue_token_pair(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def revoke_refresh_token(self, raw_refresh: str) -> None:
        """Revoca un refresh token explícitamente (logout)."""
        refresh_hash = security.hash_refresh_token(raw_refresh)
        token = await self.refresh_token_repo.get_by_token_hash(refresh_hash)
        if token is None:
            return
        await self.refresh_token_repo.revoke_all_for_user(token.user_id)


class AuthenticationError(Exception):
    """Error de autenticación (credenciales inválidas, token expirado, etc.)."""

    pass
