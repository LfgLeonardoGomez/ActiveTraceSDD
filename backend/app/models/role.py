"""Modelos Rol y Permiso: esqueletos placeholder para C-02.

Matriz de permisos y seed de datos se implementan en C-04.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class Rol(BaseModelMixin, Base):
    """Rol de usuario dentro de un tenant."""

    __tablename__ = "roles"

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)


class Permiso(BaseModelMixin, Base):
    """Permiso granular del sistema dentro de un tenant."""

    __tablename__ = "permisos"

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    modulo: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
