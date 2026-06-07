"""Schemas Pydantic para el router de autenticacion.

Todos usan extra='forbid' como regla dura del proyecto.
"""

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    """Solicitud de login."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Respuesta con par de tokens."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"


class PreAuthResponse(BaseModel):
    """Respuesta de gating 2FA: pre_auth_token temporal."""

    model_config = ConfigDict(extra="forbid")

    pre_auth_token: str


class ForgotRequest(BaseModel):
    """Solicitud de recuperacion de password."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class ResetRequest(BaseModel):
    """Restablecimiento de password con token."""

    model_config = ConfigDict(extra="forbid")

    token: str
    new_password: str


class TwoFactorVerifyRequest(BaseModel):
    """Verificacion de codigo TOTP en login."""

    model_config = ConfigDict(extra="forbid")

    pre_auth_token: str
    code: str


class TwoFactorConfirmRequest(BaseModel):
    """Confirmacion de enrollment 2FA."""

    model_config = ConfigDict(extra="forbid")

    code: str


class TwoFactorDisableRequest(BaseModel):
    """Deshabilitacion de 2FA."""

    model_config = ConfigDict(extra="forbid")

    code: str


class EnrollResponse(BaseModel):
    """Respuesta de enrollment 2FA."""

    model_config = ConfigDict(extra="forbid")

    provisioning_uri: str
    qr_base64: str


class BackupCodesResponse(BaseModel):
    """Respuesta con backup codes."""

    model_config = ConfigDict(extra="forbid")

    backup_codes: list[str]
