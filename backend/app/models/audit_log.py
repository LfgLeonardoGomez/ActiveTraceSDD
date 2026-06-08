"""Modelo AuditLog — E-AUD, append-only.

Registro inmutable de acciones significativas del sistema.
Sin updated_at ni deleted_at: la tabla no admite UPDATE ni DELETE
(enforced por trigger a nivel DB en migración 004).
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """Registro de auditoría inmutable (append-only)."""

    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    actor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    impersonado_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    # FK lógica a materias; constraint añadido en C-06 cuando exista la tabla
    materia_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        default=None,
    )
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    detalle: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    filas_afectadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True, default=None)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True, default=None)
