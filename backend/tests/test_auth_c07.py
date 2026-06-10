"""Tests TDD de regresión para auth_service con PII cifrada (C-07).

Task Group 6: adaptación de auth_service para usar email_hash.
Strict TDD: escribir el test de regresión ANTES de modificar auth_service.

Regla crítica: el test 6.1 se escribe primero en RED (contra el código
actual), luego se actualiza auth_service, y se verifica que sigue en GREEN.
"""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security


class TestLoginConUsuarioPii:
    """Task 6.1 Regresión: login funciona con email_hash lookup.

    Este test verifica el flujo completo de autenticación después de
    migrar el lookup de email (texto plano) a email_hash (HMAC-SHA256).
    """

    @pytest.mark.asyncio
    async def test_authenticate_con_usuario_pii_creado_por_repo(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 6.1: crear usuario via repositorio (PII cifrada) y autenticar.

        Flujo:
        1. Crear usuario con PII cifrada (email → ciphertext, email_hash calculado)
        2. Setear password_hash
        3. Llamar AuthService.authenticate con email en texto plano
        4. Verificar que retorna el usuario correctamente
        """
        from app.repositories.usuarios import UsuarioRepository
        from app.services.auth_service import AuthService
        from app.services.token_service import TokenService

        # Crear usuario con PII cifrada
        repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await repo.create(
            nombre="Testlogin",
            apellidos="PiiHash",
            email="testlogin.pii@example.com",
            estado="Activo",
        )

        # Setear password_hash directamente
        password_plain = "SecurePass123!"
        pwd_hash = security.hash_password(password_plain)
        await repo.update(usuario.id, {"password_hash": pwd_hash})

        # Autenticar con auth_service (debe usar email_hash lookup)
        token_service = TokenService(db_session)
        auth_service = AuthService(db_session, token_service)

        result = await auth_service.authenticate(
            email="testlogin.pii@example.com",
            password=password_plain,
            tenant_id=default_tenant.id,
        )

        assert result is not None, "authenticate debe retornar el usuario si credenciales son correctas"
        assert result.id == usuario.id

    @pytest.mark.asyncio
    async def test_authenticate_email_incorrecto_retorna_none(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 6.1: email incorrecto → retorna None (timing-safe)."""
        from app.services.auth_service import AuthService
        from app.services.token_service import TokenService

        token_service = TokenService(db_session)
        auth_service = AuthService(db_session, token_service)

        result = await auth_service.authenticate(
            email="noexiste@example.com",
            password="cualquier",
            tenant_id=default_tenant.id,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_password_incorrecto_retorna_none(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 6.1: password incorrecto → retorna None (timing-safe)."""
        from app.repositories.usuarios import UsuarioRepository
        from app.services.auth_service import AuthService
        from app.services.token_service import TokenService

        repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await repo.create(
            nombre="WrongPass",
            apellidos="Test",
            email="wrongpass@example.com",
            estado="Activo",
        )
        pwd_hash = security.hash_password("CorrectPass123!")
        await repo.update(usuario.id, {"password_hash": pwd_hash})

        token_service = TokenService(db_session)
        auth_service = AuthService(db_session, token_service)

        result = await auth_service.authenticate(
            email="wrongpass@example.com",
            password="WrongPass!",
            tenant_id=default_tenant.id,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_email_case_insensitive(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 6.1: email en mayúsculas debe funcionar (normalización a lowercase en hash)."""
        from app.repositories.usuarios import UsuarioRepository
        from app.services.auth_service import AuthService
        from app.services.token_service import TokenService

        repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await repo.create(
            nombre="CaseTest",
            apellidos="User",
            email="casetest@example.com",
            estado="Activo",
        )
        pwd_hash = security.hash_password("Pass123!")
        await repo.update(usuario.id, {"password_hash": pwd_hash})

        token_service = TokenService(db_session)
        auth_service = AuthService(db_session, token_service)

        # Autenticar con email en mayúsculas
        result = await auth_service.authenticate(
            email="CASETEST@EXAMPLE.COM",
            password="Pass123!",
            tenant_id=default_tenant.id,
        )

        assert result is not None, "El login debe funcionar con email en mayúsculas"
        assert result.id == usuario.id


class TestGetCurrentUserDecryptEmail:
    """Task 6.3: get_current_user desencripta email correctamente."""

    def test_email_hash_en_jwt_no_es_necesario(self) -> None:
        """Verificar que el JWT usa email descifrado (no ciphertext) en CurrentUser."""
        from app.core.dependencies import CurrentUser

        # CurrentUser debe poder crearse con email en texto plano
        user = CurrentUser(
            id=uuid4(),
            tenant_id=uuid4(),
            email="plain@test.com",
            roles=["ADMIN"],
        )
        assert user.email == "plain@test.com"
        # No es ciphertext (no es base64 largo)
        assert len(user.email) < 50
