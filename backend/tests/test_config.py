import os
import pytest
from pydantic import ValidationError


class TestSettings:
    """Tests de TDD para core/config.py — C-01."""

    def test_settings_instantiates_with_valid_env(self, monkeypatch):
        """RED: Settings se instancia con env válido."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        from app.core.config import Settings
        settings = Settings()
        assert settings.access_token_expire_minutes == 15
        assert str(settings.database_url).startswith("postgresql+asyncpg://")
        assert settings.secret_key == "a" * 32
        assert settings.encryption_key == "b" * 32

    def test_settings_fails_on_missing_required(self, monkeypatch):
        """RED: falla si falta una variable requerida."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        from app.core.config import Settings
        with pytest.raises(ValidationError):
            Settings()

    def test_settings_fails_on_invalid_secret_key_length(self, monkeypatch):
        """RED: falla si SECRET_KEY tiene menos de 32 caracteres."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("SECRET_KEY", "short")
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        from app.core.config import Settings
        with pytest.raises(ValidationError):
            Settings()

    def test_settings_fails_on_invalid_encryption_key_length(self, monkeypatch):
        """RED: falla si ENCRYPTION_KEY no tiene exactamente 32 caracteres."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "short")
        from app.core.config import Settings
        with pytest.raises(ValidationError):
            Settings()

    def test_settings_triangulate_invalid_type(self, monkeypatch):
        """TRIANGULATE: valor con tipo inválido (access_token_expire_minutes no es int)."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "not_an_int")
        from app.core.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "access_token_expire_minutes" in str(exc_info.value)

    def test_settings_triangulate_missing_single_var(self, monkeypatch):
        """TRIANGULATE: falta solo una variable requerida."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        from app.core.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "ENCRYPTION_KEY" in str(exc_info.value) or "encryption_key" in str(exc_info.value)
