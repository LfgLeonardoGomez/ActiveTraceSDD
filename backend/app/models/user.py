"""Modelo Usuario con campos de autenticación y PII cifrada (C-03, C-07).

C-03: password_hash (Argon2id), flag 2FA.
C-07: PII cifrada (email ciphertext, dni, cuil, cbu, alias_cbu) + email_hash para lookup.

Reglas duras:
- email almacena AES-256-GCM ciphertext (nunca texto plano)
- email_hash = HMAC-SHA256(email, ENCRYPTION_KEY) — determinístico para lookup
- dni, cuil, cbu, alias_cbu: AES-256-GCM ciphertext
- El repositorio UsuarioRepository cifra/descifra transparentemente
"""

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class Usuario(BaseModelMixin, Base):
    """Usuario de dominio con soporte de autenticación y PII cifrada."""

    __tablename__ = "usuarios"
    __table_args__ = (
        # Índice único parcial para unicidad de email por tenant (D-02)
        Index(
            "idx_usuarios_tenant_email_hash",
            "tenant_id",
            "email_hash",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    # email almacena AES-256-GCM ciphertext (C-07 D-02)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    # HMAC-SHA256 del email para lookup determinístico (D-02)
    email_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    legajo: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    is_2fa_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # PII cifrada (AES-256-GCM ciphertext) — cifrado/descifrado en UsuarioRepository
    dni: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    cuil: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    cbu: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    alias_cbu: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Perfil docente (no PII sensible — texto plano)
    banco: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    regional: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    legajo_profesional: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default=None
    )
    facturador: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)

    # tenant_id heredado de BaseModelMixin
