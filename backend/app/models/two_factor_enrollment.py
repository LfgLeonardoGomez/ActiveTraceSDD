"""Modelo TwoFactorEnrollment para 2FA TOTP.

El secreto TOTP se almacena cifrado con AES-256.
"""

from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class TwoFactorEnrollment(BaseModelMixin, Base):
    """Enrollment de 2FA TOTP para un usuario."""

    __tablename__ = "two_factor_enrollments"

    user_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    encrypted_secret: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    backup_code_hashes: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True, default=None
    )
