"""Modelos Rol, Permiso y RolPermiso para RBAC (C-04).

Matriz de permisos administrable por tenant con soft delete.
"""

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class Rol(BaseModelMixin, Base):
    """Rol de usuario dentro de un tenant."""

    __tablename__ = "roles"
    __table_args__ = (
        Index(
            "idx_roles_tenant_codigo",
            "tenant_id",
            "codigo",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)


class Permiso(BaseModelMixin, Base):
    """Permiso granular del sistema dentro de un tenant."""

    __tablename__ = "permisos"
    __table_args__ = (
        Index(
            "idx_permisos_tenant_codigo",
            "tenant_id",
            "codigo",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    modulo: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)


class RolPermiso(BaseModelMixin, Base):
    """Asignación de permiso a rol con flag propio."""

    __tablename__ = "rol_permiso"

    rol_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    permiso_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("permisos.id", ondelete="CASCADE"),
        nullable=False,
    )
    es_propio: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
