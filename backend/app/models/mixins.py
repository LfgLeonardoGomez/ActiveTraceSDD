"""Mixins base para todos los modelos ORM del dominio.

BaseModelMixin provee los campos transversales que toda entidad de negocio
debe tener: identidad UUID, tenant_id para aislamiento multi-tenant,
timestamps y soft delete.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, event
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.core.database import Base


class BaseModelMixin:
    """Mixin base para modelos de dominio (no global/tabla de lookup).

    Atributos:
        id: UUID v4 generado por aplicación.
        tenant_id: FK a tenants.id. Obligatorio para aislamiento row-level.
        created_at: timestamp de creación (UTC).
        updated_at: timestamp de última modificación (UTC).
        deleted_at: timestamp de soft delete; NULL = activo.
    """

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


@event.listens_for(Session, "before_flush", propagate=True)
def _set_updated_at_on_flush(session, flush_context, instances):
    """Hook SQLAlchemy que auto-actualiza updated_at antes de cada flush.

    Garantiza que updated_at refleje la última modificación incluso cuando
    `onupdate` de la columna no se dispare (ej. updates manuales vía ORM).
    """
    now = datetime.now(timezone.utc)
    for instance in session.dirty:
        if instance is None:
            continue
        if hasattr(instance, "updated_at"):
            # Evitar tocar instancias que ya están siendo eliminadas
            if not session.deleted or instance not in session.deleted:
                instance.updated_at = now
