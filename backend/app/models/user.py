"""Modelo Usuario: esqueleto placeholder para C-02.

Lógica de auth, JWT, 2FA, cifrado de PII se implementan en C-03/C-07.
Este modelo hereda BaseModelMixin para validar multi-tenancy y soft delete.
"""

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class Usuario(BaseModelMixin, Base):
    """Esqueleto de usuario de dominio."""

    __tablename__ = "usuarios"

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    legajo: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)

    # tenant_id heredado de BaseModelMixin
