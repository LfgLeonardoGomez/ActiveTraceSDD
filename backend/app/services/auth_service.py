"""Servicio de autenticacion: login, logout, resolucion de identidad.

No accede directamente a DB; usa repositorios.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.models.user import Usuario
from app.services.token_service import TokenService


class AuthService:
    """Servicio de autenticacion de usuarios."""

    def __init__(
        self,
        db_session: AsyncSession,
        token_service: TokenService,
    ) -> None:
        self.db_session = db_session
        self.token_service = token_service

    async def authenticate(
        self,
        email: str,
        password: str,
        tenant_id: UUID,
    ) -> Usuario | None:
        """Valida credenciales y retorna el usuario si son correctas.

        Busca por email dentro del tenant; comportamiento identico en tiempo
        para email existente e inexistente (timing-safe).
        """
        result = await self.db_session.execute(
            select(Usuario).where(
                Usuario.email == email,
                Usuario.tenant_id == tenant_id,
                Usuario.deleted_at.is_(None),
            )
        )
        user = result.scalar_one_or_none()
        if user is None or user.password_hash is None:
            # Ejecutar verify_password con hash dummy para timing-safe
            security.verify_password(password, security.DUMMY_HASH)
            return None
        if not security.verify_password(password, user.password_hash):
            return None
        return user

    async def logout(self, raw_refresh: str) -> None:
        """Revoca la sesion asociada al refresh token."""
        await self.token_service.revoke_refresh_token(raw_refresh)
