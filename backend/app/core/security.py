"""Módulo de seguridad: JWT, Argon2id, AES-256.

C-03: auth, tokens, cifrado de secrets.
"""

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings

settings = Settings()

ALGORITHM = "HS256"
NONCE_LENGTH = 12  # bytes para AES-GCM

# Argon2id via passlib
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Hash dummy para timing-safe comparison en login (nunca coincide con password real)
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$d47R+n8v5ZwTAoDwXgthbA$oV/2jeq7mzISwcwiSjJmgIrEIWw8Eiix6lat9Aa8lh0"


class SecurityError(Exception):
    """Error de seguridad (cifrado, token inválido, etc.)."""

    pass


def hash_password(plain_password: str) -> str:
    """Hashea un password con Argon2id."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica un password contra su hash con timing-safe comparison."""
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    roles: list[str],
    expires_delta: timedelta | None = None,
) -> str:
    """Crea un JWT access token con claims mínimos.

    Claims:
        sub: user UUID
        tenant_id: tenant UUID
        roles: lista de strings
        type: "access"
        iat: issued at
        exp: expiration
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_access_token(token: str) -> dict | None:
    """Verifica y decodifica un access token. Retorna None si es inválido."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except (JWTError, Exception):
        return None


def create_impersonation_token(
    actor_id: UUID,
    target_id: UUID,
    tenant_id: UUID,
    roles: list[str],
    expires_delta: timedelta | None = None,
) -> str:
    """Crea un JWT de impersonación.

    Claims adicionales vs access normal:
        imp: true — marca el token como de impersonación
        act: UUID del actor real (quien impersona)
        sub: UUID del usuario impersonado (target)
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(target_id),
        "act": str(actor_id),
        "imp": True,
        "tenant_id": str(tenant_id),
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token() -> str:
    """Genera un token opaco aleatorio de 32 bytes (URL-safe)."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(raw_token: str) -> str:
    """Genera SHA-256 de un refresh token para almacenamiento."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_pre_auth_token(
    user_id: UUID,
    tenant_id: UUID,
    expires_delta: timedelta = timedelta(minutes=5),
) -> str:
    """Crea un JWT de pre-autenticación para gating 2FA (5 min default).

    Claims:
        sub: user UUID
        tenant_id: tenant UUID
        type: "pre_auth"
        iat, exp
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "pre_auth",
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_pre_auth_token(token: str) -> dict | None:
    """Verifica un pre_auth token. Retorna None si es inválido."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "pre_auth":
            return None
        return payload
    except (JWTError, Exception):
        return None


def _get_aes_key() -> bytes:
    """Devuelve la clave AES de 32 bytes desde settings."""
    key = settings.encryption_key.encode("utf-8")
    if len(key) != 32:
        raise SecurityError("ENCRYPTION_KEY must be exactly 32 bytes")
    return key


def encrypt_aes256(plaintext: str) -> str:
    """Cifra texto plano con AES-256-GCM.

    Retorna cadena base64 con nonce + tag + ciphertext.
    """
    key = _get_aes_key()
    nonce = os.urandom(NONCE_LENGTH)
    aesgcm = AESGCM(key)
    cipher_bytes = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = nonce + cipher_bytes
    return base64.b64encode(payload).decode("ascii")


def decrypt_aes256(ciphertext: str) -> str:
    """Descifra texto cifrado con AES-256-GCM.

    Raises:
        SecurityError: Si el ciphertext es inválido o corrupto.
    """
    try:
        payload = base64.b64decode(ciphertext)
    except Exception as exc:
        raise SecurityError("Invalid base64 encoding") from exc

    if len(payload) < NONCE_LENGTH + 16:
        raise SecurityError("Ciphertext too short")

    nonce = payload[:NONCE_LENGTH]
    cipher_bytes = payload[NONCE_LENGTH:]
    key = _get_aes_key()
    aesgcm = AESGCM(key)

    try:
        plain_bytes = aesgcm.decrypt(nonce, cipher_bytes, None)
    except Exception as exc:
        raise SecurityError("Tamper detected or corrupted ciphertext") from exc

    return plain_bytes.decode("utf-8")


def hash_token_for_storage(raw_token: str) -> str:
    """Hash SHA-256 de un token opaco para almacenamiento seguro."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def compare_token_hash(raw_token: str, stored_hash: str) -> bool:
    """Compara un token raw contra su hash almacenado (timing-safe)."""
    computed = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return hmac.compare_digest(computed, stored_hash)
