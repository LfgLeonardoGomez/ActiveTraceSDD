"""Modelo Usuario con campos de autenticación (C-03).

Incluye password_hash (Argon2id) y flag de 2FA.
Este modelo hereda BaseModelMixin para validar multi-tenancy y soft delete.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class Usuario(BaseModelMixin, Base):
    """Usuario de dominio con soporte de autenticación."""

    __tablename__ = "usuarios"

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    legajo: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    is_2fa_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # tenant_id heredado de BaseModelMixin
