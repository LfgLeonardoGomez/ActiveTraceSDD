"""Modelo RateLimitBucket para rate limiting por PostgreSQL.

Tabla global (sin tenant_id) que almacena contadores atómicos por recurso + ventana.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RateLimitBucket(Base):
    """Bucket de rate limiting atómico."""

    __tablename__ = "rate_limit_buckets"

    resource: Mapped[str] = mapped_column(String(255), nullable=False, primary_key=True)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, primary_key=True
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
