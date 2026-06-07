"""Tests de TDD para app/core/security.py — C-03 Task 2.1 / 2.2.

Capas: core/security
SAFETY NET: pytest sin fallas previas ✓
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt, JWTError

from app.core.config import Settings
from app.core import security

settings = Settings()


class TestHashPassword:
    """RED: hash_password produce hash Argon2id."""

    def test_hash_password_returns_string(self):
        """RED: hash_password retorna un string."""
        hashed = security.hash_password("plain123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_salts(self):
        """TRIANGULATE: dos hashes del mismo password son distintos."""
        h1 = security.hash_password("plain123")
        h2 = security.hash_password("plain123")
        assert h1 != h2


class TestVerifyPassword:
    """GREEN: verify_password valida correctamente."""

    def test_verify_password_correct(self):
        """GREEN: password correcto retorna True."""
        hashed = security.hash_password("plain123")
        assert security.verify_password("plain123", hashed) is True

    def test_verify_password_incorrect(self):
        """TRIANGULATE: password incorrecto retorna False."""
        hashed = security.hash_password("plain123")
        assert security.verify_password("wrong", hashed) is False

    def test_verify_password_timing_safe(self):
        """TRIANGULATE: tiempo de respuesta similar para correcto/incorrecto."""
        import time

        hashed = security.hash_password("plain123")
        times_correct = []
        times_incorrect = []
        for _ in range(10):
            t0 = time.perf_counter()
            security.verify_password("plain123", hashed)
            t1 = time.perf_counter()
            times_correct.append(t1 - t0)

            t0 = time.perf_counter()
            security.verify_password("wrong", hashed)
            t1 = time.perf_counter()
            times_incorrect.append(t1 - t0)

        avg_correct = sum(times_correct) / len(times_correct)
        avg_incorrect = sum(times_incorrect) / len(times_incorrect)
        # Deben estar dentro de 2x (timing-safe comparison)
        ratio = max(avg_correct, avg_incorrect) / max(min(avg_correct, avg_incorrect), 1e-9)
        assert ratio < 2.0


class TestCreateAccessToken:
    """RED: create_access_token emite JWT con claims mínimos."""

    def test_create_access_token_returns_string(self):
        token = security.create_access_token(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            roles=[],
        )
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # header.payload.signature

    def test_access_token_claims(self):
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        token = security.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=["admin"],
        )
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[security.ALGORITHM]
        )
        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["roles"] == ["admin"]
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_access_token_expiration(self):
        token = security.create_access_token(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            roles=[],
            expires_delta=timedelta(minutes=1),
        )
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[security.ALGORITHM]
        )
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        assert exp > now
        assert exp < now + timedelta(minutes=2)


class TestVerifyAccessToken:
    """GREEN: verify_access_token decodifica y valida."""

    def test_verify_valid_token(self):
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        token = security.create_access_token(
            user_id=user_id, tenant_id=tenant_id, roles=["admin"]
        )
        payload = security.verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)

    def test_verify_expired_token(self):
        token = security.create_access_token(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            roles=[],
            expires_delta=timedelta(seconds=-1),
        )
        payload = security.verify_access_token(token)
        assert payload is None

    def test_verify_invalid_signature(self):
        token = security.create_access_token(
            user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), roles=[]
        )
        # Corromper token
        tampered = token[:-5] + "XXXXX"
        payload = security.verify_access_token(tampered)
        assert payload is None


class TestCreateRefreshToken:
    """RED: create_refresh_token emite token opaco."""

    def test_create_refresh_token_returns_string(self):
        token = security.create_refresh_token()
        assert isinstance(token, str)
        assert len(token) > 32

    def test_create_refresh_token_unique(self):
        t1 = security.create_refresh_token()
        t2 = security.create_refresh_token()
        assert t1 != t2


class TestCreatePreAuthToken:
    """RED: create_pre_auth_token para gating 2FA."""

    def test_pre_auth_token_claims(self):
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        token = security.create_pre_auth_token(user_id, tenant_id)
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[security.ALGORITHM]
        )
        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["type"] == "pre_auth"
        assert "exp" in payload

    def test_pre_auth_token_short_expiry(self):
        token = security.create_pre_auth_token(
            uuid.uuid4(), uuid.uuid4()
        )
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[security.ALGORITHM]
        )
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        # Debe expirar en ~5 minutos
        assert exp > now + timedelta(minutes=4)
        assert exp < now + timedelta(minutes=6)


class TestEncryptDecrypt:
    """GREEN: AES-256 para secrets."""

    def test_encrypt_decrypt_roundtrip(self):
        plain = "my-secret-totp-key"
        cipher = security.encrypt_aes256(plain)
        assert cipher != plain
        decrypted = security.decrypt_aes256(cipher)
        assert decrypted == plain

    def test_decrypt_tampered_raises(self):
        cipher = security.encrypt_aes256("secret")
        tampered = cipher[:-5] + "xxxxx"
        with pytest.raises(security.SecurityError):
            security.decrypt_aes256(tampered)
