"""Servicio de autenticacion: login, logout, resolucion de identidad.

No accede directamente a DB; usa repositorios.

C-07: lookup de email via HMAC-SHA256 (email_hash) en lugar de texto plano.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.models.user import Usuario
from app.repositories.usuarios import UsuarioRepository
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

        Busca por email_hash (HMAC-SHA256) dentro del tenant.
        Comportamiento identico en tiempo para email existente e inexistente (timing-safe).

        C-07 D-02: email lookup vía hash determinístico — NO texto plano.
        """
        repo = UsuarioRepository(self.db_session, tenant_id)
        user = await repo.get_by_email_hash(email)

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
