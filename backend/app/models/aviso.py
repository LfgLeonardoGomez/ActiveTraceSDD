"""Modelos ORM para avisos y acknowledgment (C-15).

E15 del modelo de datos: Aviso (anuncio dirigido) y AcknowledgmentAviso
(confirmación de lectura por parte del usuario).

Reglas duras:
- Multi-tenant row-level: tenant_id en todas las entidades.
- Soft delete via BaseModelMixin (deleted_at).
- AlcanceAviso: Global | PorMateria | PorCohorte | PorRol.
- SeveridadAviso: Info | Advertencia | Crítico.
- rol_destino NULL = "all roles" (D-02 del design).
- AcknowledgmentAviso: upsert idempotente por (aviso_id, usuario_id).
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class AlcanceAviso(StrEnum):
    GLOBAL = "Global"
    POR_MATERIA = "PorMateria"
    POR_COHORTE = "PorCohorte"
    POR_ROL = "PorRol"


class SeveridadAviso(StrEnum):
    INFO = "Info"
    ADVERTENCIA = "Advertencia"
    CRITICO = "Crítico"


class Aviso(BaseModelMixin, Base):
    """Anuncio dirigido a segmentos de la comunidad académica.

    Alcance determina quién puede ver el aviso:
    - Global: todos los usuarios del tenant.
    - PorMateria: usuarios con asignación activa en materia_id.
    - PorCohorte: usuarios con asignación activa en cohorte_id.
    - PorRol: usuarios cuyo rol coincide con rol_destino (NULL = todos).
    """

    __tablename__ = "aviso"
    __table_args__ = (
        Index("ix_aviso_tenant", "tenant_id"),
        Index(
            "ix_aviso_tenant_activo_vigencia",
            "tenant_id",
            "activo",
            "inicio_en",
            "fin_en",
        ),
        Index(
            "ix_aviso_alcance",
            "tenant_id",
            "alcance",
            "materia_id",
            "cohorte_id",
        ),
    )

    alcance: Mapped[str] = mapped_column(String(30), nullable=False)
    materia_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="SET NULL"),
        nullable=True,
    )
    cohorte_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="SET NULL"),
        nullable=True,
    )
    rol_destino: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    severidad: Mapped[str] = mapped_column(String(30), nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    inicio_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    fin_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    orden: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    requiere_ack: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )


class AcknowledgmentAviso(BaseModelMixin, Base):
    """Confirmación de lectura de un aviso por un usuario.

    Idempotente por (aviso_id, usuario_id) — la PK compuesta lógica
    se refuerza con UniqueConstraint.
    """

    __tablename__ = "acknowledgment_aviso"
    __table_args__ = (
        UniqueConstraint(
            "aviso_id", "usuario_id", name="uq_ack_aviso_usuario"
        ),
        Index("ix_ack_aviso_aviso", "aviso_id"),
        Index("ix_ack_aviso_usuario", "usuario_id"),
    )

    aviso_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("aviso.id", ondelete="CASCADE"),
        nullable=False,
    )
    usuario_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    confirmado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
