"""Configuración tipada del proyecto vía Pydantic Settings v2.

Carga desde variables de entorno y/o archivo `.env`.
Valida en arranque: valores inválidos o variables requeridas ausentes
impiden que la aplicación inicie.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings de activia-trace."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    database_url: str = Field(..., description="URL de conexión a PostgreSQL")
    secret_key: str = Field(..., description="Clave de firma JWT (mínimo 32 caracteres)")
    encryption_key: str = Field(..., description="Clave AES-256 (exactamente 32 caracteres)")
    access_token_expire_minutes: int = Field(
        default=15, description="Expiración del access token en minutos"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Expiracion del refresh token en dias"
    )
    refresh_cookie_secure: bool = Field(
        default=True, description="Flag Secure en cookie de refresh token"
    )
    moodle_url: str | None = Field(default=None, description="URL base de Moodle WS")
    moodle_token: str | None = Field(default=None, description="Token de Moodle WS")

    @field_validator("secret_key")
    @classmethod
    def _validate_secret_key_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("encryption_key")
    @classmethod
    def _validate_encryption_key_length(cls, v: str) -> str:
        if len(v) != 32:
            raise ValueError("ENCRYPTION_KEY must be exactly 32 characters long")
        return v
