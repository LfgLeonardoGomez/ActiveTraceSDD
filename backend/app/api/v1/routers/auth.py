"""Router de autenticacion: login, refresh, logout, forgot, reset, 2FA.

Todos los endpoints de autenticacion bajo /api/auth.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import Settings
from app.core.dependencies import CurrentUser, get_current_active_user, get_db
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import Usuario
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.repositories.rate_limit_repository import RateLimitRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.two_factor_repository import TwoFactorRepository
from app.schemas.auth import (
    BackupCodesResponse,
    EnrollResponse,
    ForgotRequest,
    LoginRequest,
    PreAuthResponse,
    ResetRequest,
    TokenResponse,
    TwoFactorConfirmRequest,
    TwoFactorDisableRequest,
    TwoFactorVerifyRequest,
)
from app.services.auth_service import AuthService
from app.services.rate_limit_service import RateLimitService
from app.services.token_service import AuthenticationError, TokenService
from app.services.two_factor_service import TwoFactorService

settings = Settings()

router = APIRouter(prefix="/api/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _get_client_ip(request: Request) -> str:
    """Extrae IP del cliente desde headers o conexion."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


def _set_refresh_cookie(response: Response, raw_refresh: str) -> None:
    """Setea cookie HttpOnly con el refresh token."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
        path="/api/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Limpia cookie de refresh token."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value="",
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
        max_age=0,
        path="/api/auth/refresh",
    )


async def _check_rate_limit(
    db: AsyncSession,
    endpoint: str,
    ip: str,
    identifier: str,
) -> None:
    """Aplica rate limiting; lanza 429 si excede."""
    rate_limit_repo = RateLimitRepository(db)
    rate_limit_service = RateLimitService(rate_limit_repo)
    resource = rate_limit_service.build_resource_key(endpoint, ip, identifier)
    permitted, retry_after = await rate_limit_service.check_limit(
        resource, max_requests=5, window_seconds=60
    )
    if not permitted:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


@router.post("/login", response_model=TokenResponse | PreAuthResponse)
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse | PreAuthResponse:
    """Login con email + password. Emite tokens o pre_auth_token si 2FA."""
    ip = _get_client_ip(request)
    await _check_rate_limit(db, "login", ip, body.email)

    # Buscar usuario por email (necesitamos tenant_id; por ahora usamos un lookup)
    # En MVP, asumimos un tenant default si no se provee. Pero esto es un hack.
    # El dominio real requiere conocer el tenant antes del login.
    # Solucion: el email es unico global o buscamos en todos los tenants.
    # Segun el spec, authenticate(email, password, tenant_id) requiere tenant_id.
    # Como no tenemos un selector de tenant en login, buscamos por email globalmente
    # y validamos password contra el usuario encontrado.
    # Esto NO es multi-tenant estricto pero es necesario para login sin contexto previo.
    result = await db.execute(
        select(Usuario).where(
            Usuario.email == body.email,
            Usuario.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    if user is None or user.password_hash is None:
        # Delay constante para timing-safe enumeration (dummy hash valido)
        security.verify_password(body.password, security.DUMMY_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not security.verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if user.is_2fa_enabled:
        pre_auth = security.create_pre_auth_token(user.id, user.tenant_id)
        return PreAuthResponse(pre_auth_token=pre_auth)

    refresh_repo = RefreshTokenRepository(db, user.tenant_id)
    token_service = TokenService(refresh_repo)
    access_token, raw_refresh = await token_service.issue_token_pair(
        user=user,
        ip_address=ip,
        user_agent=_get_user_agent(request),
    )
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    raw_refresh: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
) -> TokenResponse:
    """Rota refresh token. Lee de cookie HttpOnly."""
    if not raw_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    # Necesitamos tenant_id para el repo. No lo tenemos directamente.
    # TokenService.rotate_refresh_token busca el token por hash y obtiene tenant_id.
    # Pero RefreshTokenRepository requiere tenant_id en constructor.
    # Solucion: buscar el token raw primero para obtener tenant_id.
    refresh_hash = security.hash_refresh_token(raw_refresh)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == refresh_hash)
    )
    token_row = result.scalar_one_or_none()
    if token_row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    refresh_repo = RefreshTokenRepository(db, token_row.tenant_id)
    token_service = TokenService(refresh_repo)
    try:
        access_token, new_raw_refresh = await token_service.rotate_refresh_token(
            raw_refresh=raw_refresh,
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    _set_refresh_cookie(response, new_raw_refresh)
    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    raw_refresh: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
) -> None:
    """Revoca sesion actual. Lee refresh de cookie HttpOnly y limpia cookie."""
    if raw_refresh:
        refresh_hash = security.hash_refresh_token(raw_refresh)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == refresh_hash)
        )
        token_row = result.scalar_one_or_none()
        if token_row:
            refresh_repo = RefreshTokenRepository(db, token_row.tenant_id)
            token_service = TokenService(refresh_repo)
            await token_service.revoke_refresh_token(raw_refresh)
    _clear_refresh_cookie(response)
    return None


@router.post("/forgot", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request: Request,
    body: ForgotRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Solicita recuperacion de password. Loggea token en consola (modo dev)."""
    ip = _get_client_ip(request)
    await _check_rate_limit(db, "forgot", ip, body.email)

    result = await db.execute(
        select(Usuario).where(
            Usuario.email == body.email,
            Usuario.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    if user is not None:
        import secrets

        raw_token = secrets.token_urlsafe(32)
        token_hash = security.hash_token_for_storage(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        reset_repo = PasswordResetTokenRepository(db, user.tenant_id)
        await reset_repo.create_reset_token(
            token_hash=token_hash,
            user_id=user.id,
            expires_at=expires_at,
        )

        # Log estructurado en consola (modo dev) — decision OQ-01
        import logging

        logger = logging.getLogger("auth")
        logger.info(
            "password_reset_token_generated",
            extra={
                "user_id": str(user.id),
                "tenant_id": str(user.tenant_id),
                "token": raw_token,
            },
        )

    return None


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: ResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Restablece password con token de recuperacion."""
    token_hash = security.hash_token_for_storage(body.token)
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.deleted_at.is_(None),
        )
    )
    token_row = result.scalar_one_or_none()

    if token_row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )

    if token_row.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token already used",
        )

    if token_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expired",
        )

    # Validar complejidad de password
    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters",
        )

    # Actualizar password
    result_user = await db.execute(
        select(Usuario).where(
            Usuario.id == token_row.user_id,
            Usuario.tenant_id == token_row.tenant_id,
            Usuario.deleted_at.is_(None),
        )
    )
    user = result_user.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    user.password_hash = security.hash_password(body.new_password)

    # Marcar token como usado
    reset_repo = PasswordResetTokenRepository(db, token_row.tenant_id)
    await reset_repo.mark_used(token_hash)

    # Invalidar todos los refresh tokens del usuario
    refresh_repo = RefreshTokenRepository(db, token_row.tenant_id)
    await refresh_repo.revoke_all_for_user(token_row.user_id)

    await db.commit()
    return None


@router.post("/2fa/enroll", response_model=EnrollResponse)
async def enroll_2fa(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnrollResponse:
    """Inicia enrollment de 2FA. Requiere auth."""
    result = await db.execute(
        select(Usuario).where(
            Usuario.id == current_user.id,
            Usuario.tenant_id == current_user.tenant_id,
            Usuario.deleted_at.is_(None),
        )
    )
    user = result.scalar_one()

    two_factor_repo = TwoFactorRepository(db, current_user.tenant_id)
    two_factor_service = TwoFactorService(db, two_factor_repo)
    return EnrollResponse(**await two_factor_service.enroll(user))


@router.post("/2fa/enroll/confirm", response_model=BackupCodesResponse)
async def confirm_enroll_2fa(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    body: TwoFactorConfirmRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BackupCodesResponse:
    """Confirma enrollment de 2FA con codigo TOTP. Requiere auth."""
    result = await db.execute(
        select(Usuario).where(
            Usuario.id == current_user.id,
            Usuario.tenant_id == current_user.tenant_id,
            Usuario.deleted_at.is_(None),
        )
    )
    user = result.scalar_one()

    two_factor_repo = TwoFactorRepository(db, current_user.tenant_id)
    two_factor_service = TwoFactorService(db, two_factor_repo)
    try:
        codes = await two_factor_service.confirm_enroll(user, body.code)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return BackupCodesResponse(backup_codes=codes)


@router.post("/2fa/verify", response_model=TokenResponse)
async def verify_2fa(
    request: Request,
    response: Response,
    body: TwoFactorVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Verifica TOTP tras login con pre_auth_token."""
    ip = _get_client_ip(request)
    # Hashear pre_auth_token para evitar exceder limite de 255 chars en resource key
    token_hash_for_rl = security.hash_token_for_storage(body.pre_auth_token)
    await _check_rate_limit(db, "2fa_verify", ip, token_hash_for_rl)

    payload = security.verify_pre_auth_token(body.pre_auth_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired pre-auth token",
        )

    user_id = UUID(payload["sub"])
    tenant_id = UUID(payload["tenant_id"])

    result = await db.execute(
        select(Usuario).where(
            Usuario.id == user_id,
            Usuario.tenant_id == tenant_id,
            Usuario.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    two_factor_repo = TwoFactorRepository(db, tenant_id)
    two_factor_service = TwoFactorService(db, two_factor_repo)

    # Verificar TOTP o backup code
    valid_totp = await two_factor_service.verify_totp(user, body.code)
    valid_backup = await two_factor_service.verify_backup_code(user, body.code)

    if not valid_totp and not valid_backup:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA code",
        )

    refresh_repo = RefreshTokenRepository(db, tenant_id)
    token_service = TokenService(refresh_repo)
    access_token, raw_refresh = await token_service.issue_token_pair(
        user=user,
        ip_address=ip,
        user_agent=_get_user_agent(request),
    )
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access_token)


@router.post("/2fa/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_2fa(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    body: TwoFactorDisableRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Deshabilita 2FA. Requiere auth y codigo TOTP valido."""
    result = await db.execute(
        select(Usuario).where(
            Usuario.id == current_user.id,
            Usuario.tenant_id == current_user.tenant_id,
            Usuario.deleted_at.is_(None),
        )
    )
    user = result.scalar_one()

    two_factor_repo = TwoFactorRepository(db, current_user.tenant_id)
    two_factor_service = TwoFactorService(db, two_factor_repo)
    try:
        await two_factor_service.disable_2fa(user, body.code)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return None
