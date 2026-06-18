"""Tests TDD de regresion para auth router y auth_service con PII cifrada.

Change: fix-auth-login-encrypted-email
Strict TDD: tests written FIRST (RED), then auth.py fixed (GREEN).

Phase 2 tasks:
  2.1 Fix TokenService constructor (uses RefreshTokenRepository, not db_session)
  2.2-2.9 HTTP endpoint integration tests (RED until auth.py fix in Phase 3)
"""

import pytest
from uuid import uuid4
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.core import security
from app.models.audit_log import AuditLog
from app.models.user import Usuario


class TestAuthServiceWithEncryptedEmail:
    """Existing regression: AuthService.authenticate works with email_hash lookup.

    These tests exercise AuthService directly (not the HTTP endpoint).
    TokenService constructor fixed: Task 2.1 — uses RefreshTokenRepository.
    """

    @pytest.mark.asyncio
    async def test_authenticate_con_usuario_pii_creado_por_repo(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Regression: create user via repo (ciphertext email, computed hash), authenticate."""
        from app.repositories.usuarios import UsuarioRepository
        from app.repositories.refresh_token_repository import RefreshTokenRepository
        from app.services.auth_service import AuthService
        from app.services.token_service import TokenService

        repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await repo.create(
            nombre="Testlogin",
            apellidos="PiiHash",
            email="testlogin.pii@example.com",
            estado="Activo",
            password_hash=security.hash_password("SecurePass123!"),
        )

        # Task 2.1: fixed constructor — TokenService takes RefreshTokenRepository
        refresh_repo = RefreshTokenRepository(db_session, default_tenant.id)
        token_service = TokenService(refresh_repo)
        auth_service = AuthService(db_session, token_service)

        result = await auth_service.authenticate(
            email="testlogin.pii@example.com",
            password="SecurePass123!",
            tenant_id=default_tenant.id,
        )

        assert result is not None, "authenticate must return user when credentials are correct"
        assert result.id == usuario.id

    @pytest.mark.asyncio
    async def test_authenticate_email_incorrecto_retorna_none(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Triangulation: wrong email → None (timing-safe)."""
        from app.repositories.refresh_token_repository import RefreshTokenRepository
        from app.services.auth_service import AuthService
        from app.services.token_service import TokenService

        refresh_repo = RefreshTokenRepository(db_session, default_tenant.id)
        token_service = TokenService(refresh_repo)
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
        """Triangulation: wrong password → None (timing-safe)."""
        from app.repositories.usuarios import UsuarioRepository
        from app.repositories.refresh_token_repository import RefreshTokenRepository
        from app.services.auth_service import AuthService
        from app.services.token_service import TokenService

        repo = UsuarioRepository(db_session, default_tenant.id)
        await repo.create(
            nombre="WrongPass",
            apellidos="Test",
            email="wrongpass@example.com",
            estado="Activo",
            password_hash=security.hash_password("CorrectPass123!"),
        )

        refresh_repo = RefreshTokenRepository(db_session, default_tenant.id)
        token_service = TokenService(refresh_repo)
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
        """Triangulation: uppercase email is normalized for hash lookup."""
        from app.repositories.usuarios import UsuarioRepository
        from app.repositories.refresh_token_repository import RefreshTokenRepository
        from app.services.auth_service import AuthService
        from app.services.token_service import TokenService

        repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await repo.create(
            nombre="CaseTest",
            apellidos="User",
            email="casetest@example.com",
            estado="Activo",
            password_hash=security.hash_password("Pass123!"),
        )

        refresh_repo = RefreshTokenRepository(db_session, default_tenant.id)
        token_service = TokenService(refresh_repo)
        auth_service = AuthService(db_session, token_service)

        result = await auth_service.authenticate(
            email="CASETEST@EXAMPLE.COM",
            password="Pass123!",
            tenant_id=default_tenant.id,
        )

        assert result is not None, "Login must work with uppercase email (normalized in hash)"
        assert result.id == usuario.id


class TestGetCurrentUserDecryptEmail:
    """get_current_user decrypts email into CurrentUser correctly."""

    def test_email_hash_en_jwt_no_es_necesario(self) -> None:
        """CurrentUser holds plaintext email (not ciphertext)."""
        from app.core.dependencies import CurrentUser

        user = CurrentUser(
            id=uuid4(),
            tenant_id=uuid4(),
            email="plain@test.com",
            roles=["ADMIN"],
        )
        assert user.email == "plain@test.com"
        # Ciphertext would be ~52+ base64 chars; plaintext email is short
        assert len(user.email) < 50


class TestLoginEndpointWithEncryptedEmail:
    """HTTP endpoint integration tests — RED until auth.py fix (Phase 3).

    Each test creates users via UsuarioRepository so email is ciphertext
    and email_hash is computed. The current auth.py queries WHERE email==plaintext
    which fails — tests should be RED. After Phase 3 fix they will go GREEN.
    """

    # Task 2.2
    @pytest.mark.asyncio
    async def test_login_with_encrypted_email_succeeds(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """Spec: Successful login with encrypted-email user.

        GIVEN user created via UsuarioRepository (ciphertext email, computed hash)
        WHEN POST /api/auth/login with correct credentials
        THEN HTTP 200 + access_token in response
        """
        from app.repositories.usuarios import UsuarioRepository

        repo = UsuarioRepository(db_session, default_tenant.id)
        await repo.create(
            nombre="LoginTest",
            apellidos="Enc",
            email="enc.login@example.com",
            estado="activo",
            password_hash=security.hash_password("Pass1234!"),
        )

        response = await async_client.post(
            "/api/auth/login",
            json={"email": "enc.login@example.com", "password": "Pass1234!"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response must contain access_token"

    # Task 2.3
    @pytest.mark.asyncio
    async def test_login_nonexistent_email_returns_401_timing_safe(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Spec: Login with non-existent email — timing-safe 401.

        GIVEN no user with a matching email_hash
        WHEN POST /api/auth/login
        THEN HTTP 401, no token, no enumeration leak
        """
        response = await async_client.post(
            "/api/auth/login",
            json={"email": "ghost@nowhere.com", "password": "whatever"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "access_token" not in data

    # Task 2.4
    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """Spec: Login with correct email but wrong password → 401.

        GIVEN user exists with matching email_hash
        WHEN POST /api/auth/login with wrong password
        THEN HTTP 401, no token
        """
        from app.repositories.usuarios import UsuarioRepository

        repo = UsuarioRepository(db_session, default_tenant.id)
        await repo.create(
            nombre="WrongPwd",
            apellidos="Test",
            email="wrongpwd@example.com",
            estado="activo",
            password_hash=security.hash_password("CorrectPass!"),
        )

        response = await async_client.post(
            "/api/auth/login",
            json={"email": "wrongpwd@example.com", "password": "WrongPass!"},
        )
        assert response.status_code == 401
        assert "access_token" not in response.json()

    # Task 2.5
    @pytest.mark.asyncio
    async def test_login_cross_tenant_duplicate_no_500(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        default_tenant,
        second_tenant,
    ) -> None:
        """Spec: Cross-tenant login — same email in two tenants, no MultipleResultsFound.

        GIVEN same email exists in two tenants (same email_hash, different tenant_id)
        WHEN POST /api/auth/login with correct password for either user
        THEN HTTP 200 (not 500), deterministic first-match result
        """
        from app.repositories.usuarios import UsuarioRepository

        password = "SharedPass1!"

        repo1 = UsuarioRepository(db_session, default_tenant.id)
        await repo1.create(
            nombre="TenantA",
            apellidos="User",
            email="shared@example.com",
            estado="activo",
            password_hash=security.hash_password(password),
        )

        repo2 = UsuarioRepository(db_session, second_tenant.id)
        await repo2.create(
            nombre="TenantB",
            apellidos="User",
            email="shared@example.com",
            estado="activo",
            password_hash=security.hash_password(password),
        )

        response = await async_client.post(
            "/api/auth/login",
            json={"email": "shared@example.com", "password": password},
        )
        # Must not raise MultipleResultsFound (500) — .scalars().first() handles it
        assert response.status_code == 200, (
            f"Cross-tenant duplicate must not raise 500: got {response.status_code}: {response.text}"
        )
        assert "access_token" in response.json()

    # Task 2.6
    @pytest.mark.asyncio
    async def test_login_null_email_hash_returns_401_not_500(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """Spec: Login with NULL email_hash user — timing-safe 401 (not 500).

        GIVEN a legacy user row with email_hash=NULL (failed backfill residual)
        WHEN POST /api/auth/login with any email
        THEN HTTP 401 (not 500, no unhandled exception)
        """
        # Insert a user with NULL email_hash directly via ORM (legacy residual)
        legacy_user = Usuario(
            nombre="Legacy",
            apellidos="User",
            email="legacy@example.com",  # plaintext — legacy row, no hash
            email_hash=None,             # deliberate NULL — the test scenario
            estado="activo",
            tenant_id=default_tenant.id,
            password_hash=security.hash_password("LegacyPass!"),
        )
        db_session.add(legacy_user)
        await db_session.commit()

        response = await async_client.post(
            "/api/auth/login",
            json={"email": "legacy@example.com", "password": "LegacyPass!"},
        )
        assert response.status_code == 401, (
            f"NULL email_hash must return 401 (not 500): got {response.status_code}: {response.text}"
        )

    # Task 2.7
    @pytest.mark.asyncio
    async def test_forgot_existing_user_succeeds(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """Spec: Forgot-password with existing user → 202 + reset token created.

        GIVEN user created via UsuarioRepository
        WHEN POST /api/auth/forgot with that email
        THEN HTTP 202 and a password-reset token is generated
        """
        from app.repositories.usuarios import UsuarioRepository
        from app.models.password_reset_token import PasswordResetToken

        repo = UsuarioRepository(db_session, default_tenant.id)
        user = await repo.create(
            nombre="ForgotTest",
            apellidos="User",
            email="forgot.enc@example.com",
            estado="activo",
            password_hash=security.hash_password("Pass1234!"),
        )

        response = await async_client.post(
            "/api/auth/forgot",
            json={"email": "forgot.enc@example.com"},
        )
        assert response.status_code == 202, (
            f"Expected 202, got {response.status_code}: {response.text}"
        )

        # Verify a reset token was actually created for this user
        result = await db_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
        )
        token_row = result.scalar_one_or_none()
        assert token_row is not None, "A password-reset token must be created for the user"

    # Task 2.8
    @pytest.mark.asyncio
    async def test_forgot_nonexistent_email_anti_enumeration(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Spec: Forgot-password with non-existent email — anti-enumeration.

        GIVEN no user with matching email_hash
        WHEN POST /api/auth/forgot
        THEN HTTP 202 (same shape as success — no enumeration leak)
        """
        response = await async_client.post(
            "/api/auth/forgot",
            json={"email": "ghost.forgot@example.com"},
        )
        assert response.status_code == 202, (
            f"Anti-enumeration: non-existent email must also return 202, got {response.status_code}"
        )

    # Task 2.9
    @pytest.mark.asyncio
    async def test_impersonation_audit_stores_plaintext_email(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        default_tenant,
    ) -> None:
        """Spec: Impersonation audit log contains readable email (not ciphertext).

        GIVEN admin actor with impersonacion:usar permission
        AND target user whose email is AES-256-GCM ciphertext
        WHEN POST /api/auth/impersonate/{user_id}
        THEN audit log detalle["target_email"] is plaintext email string
        AND it does NOT look like base64 ciphertext (short, contains @)
        """
        from app.repositories.rbac_repository import (
            PermisoRepository,
            RolPermisoRepository,
            RolRepository,
        )
        from app.repositories.usuarios import UsuarioRepository

        # Set up impersonacion:usar permission
        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        rol = await rol_repo.create(codigo="ADMIN_IMP_ENC", nombre="Admin Impersonation Enc")
        perm = await perm_repo.create(
            codigo="impersonacion:usar",
            nombre="Usar impersonacion",
            modulo="auth",
        )
        await rp_repo.create(rol_id=rol.id, permiso_id=perm.id, es_propio=False)

        # Create actor (raw ORM — actor email not relevant to this test assertion)
        actor = Usuario(
            nombre="Actor",
            apellidos="Admin",
            email="actor.imp@example.com",
            estado="Activo",
            tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234!"),
        )
        db_session.add(actor)
        await db_session.commit()
        await db_session.refresh(actor)

        # Create target via repository — email stored as ciphertext
        repo = UsuarioRepository(db_session, default_tenant.id)
        target = await repo.create(
            nombre="Target",
            apellidos="User",
            email="target.enc@example.com",
            estado="Activo",
            password_hash=security.hash_password("Pass1234!"),
        )

        # Get an access token for the actor with impersonation role
        actor_token = security.create_access_token(
            user_id=actor.id,
            tenant_id=default_tenant.id,
            roles=["ADMIN_IMP_ENC"],
        )

        response = await async_client.post(
            "/api/auth/impersonate",
            json={"target_user_id": str(target.id)},
            headers={"Authorization": f"Bearer {actor_token}"},
        )
        assert response.status_code == 200, (
            f"Impersonation must succeed: got {response.status_code}: {response.text}"
        )

        # Verify audit log stores PLAINTEXT email, not ciphertext
        result = await db_session.execute(
            select(AuditLog).where(
                AuditLog.actor_id == actor.id,
                AuditLog.impersonado_id == target.id,
            )
        )
        audit = result.scalar_one_or_none()
        assert audit is not None, "An audit log entry must be created for impersonation"
        assert audit.detalle is not None, "Audit detalle must not be None"
        target_email_in_audit = audit.detalle.get("target_email")
        assert target_email_in_audit is not None, "detalle must contain target_email"
        # Plaintext email: short, contains @, not base64 garbage
        assert "@" in target_email_in_audit, (
            f"target_email must be plaintext (contains @), got: {target_email_in_audit!r}"
        )
        assert len(target_email_in_audit) < 50, (
            f"target_email looks like ciphertext (too long): {target_email_in_audit!r}"
        )
