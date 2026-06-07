"""Modelo RefreshToken para rotación de sesiones.

Cada refresh token se almacena hasheado (SHA-256); el raw nunca se guarda.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class RefreshToken(BaseModelMixin, Base):
    """Token de refresco persistente con rotación y revocación."""

    __tablename__ = "refresh_tokens"

    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True, default=None
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
