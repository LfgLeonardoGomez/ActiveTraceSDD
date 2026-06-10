"""Modelos ORM para el padrón de alumnos versionado (C-09).

E6 del modelo de datos:
- VersionPadron: historial versionado de cargas por materia × cohorte.
  Solo una versión puede estar activa por (tenant_id, materia_id, cohorte_id).
- EntradaPadron: alumno en una versión del padrón.
  email almacena AES-256-GCM ciphertext (cifrado/descifrado en PadronRepository).
  usuario_id es nullable — puede existir antes de que el alumno tenga cuenta.

Reglas:
- Al activar una nueva versión, la anterior se desactiva (sin borrado físico).
- Soft delete transversal heredado de BaseModelMixin.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class VersionPadron(BaseModelMixin, Base):
    """Versión del padrón de alumnos para una materia × cohorte.

    Solo una versión activa por (tenant_id, materia_id, cohorte_id).
    La activación de una nueva versión desactiva la anterior sin borrarla.
    """

    __tablename__ = "versiones_padron"
    __table_args__ = (
        Index(
            "ix_versiones_padron_tenant_materia_cohorte",
            "tenant_id",
            "materia_id",
            "cohorte_id",
        ),
        Index(
            "ix_versiones_padron_activa",
            "tenant_id",
            "materia_id",
            "cohorte_id",
            "activa",
        ),
    )

    materia_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cohorte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cargado_por: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cargado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    origen: Mapped[str] = mapped_column(
        String(20), nullable=False, default="manual"
    )


class EntradaPadron(BaseModelMixin, Base):
    """Entrada individual del padrón: un alumno en una versión.

    email almacena AES-256-GCM ciphertext — cifrado/descifrado SOLO en
    PadronRepository (nunca en texto plano en DB ni en logs).

    usuario_id es nullable: puede existir antes de que el alumno tenga
    cuenta de usuario en el sistema.
    """

    __tablename__ = "entradas_padron"
    __table_args__ = (
        Index("ix_entradas_padron_version_id", "version_id"),
        Index("ix_entradas_padron_tenant_id", "tenant_id"),
        Index("ix_entradas_padron_usuario_id", "usuario_id"),
    )

    version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("versiones_padron.id", ondelete="RESTRICT"),
        nullable=False,
    )
    usuario_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    # email almacena AES-256-GCM ciphertext (C-09)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    comision: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    regional: Mapped[str] = mapped_column(String(100), nullable=False, default="")
