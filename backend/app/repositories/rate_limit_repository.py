"""Repository para RateLimitBucket (global, sin tenant_id).

Rate limiting atómico basado en PostgreSQL.
"""

from datetime import datetime, timezone

from sqlalchemy import insert, select, update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import Base
from app.models.rate_limit_bucket import RateLimitBucket


class RateLimitRepository:
    """Repositorio de buckets de rate limiting."""

    def __init__(self, db_session) -> None:
        self.db_session = db_session

    async def increment(self, resource: str, window_start: datetime) -> int:
        """Incrementa el contador de un bucket y retorna el nuevo count.

        Usa INSERT ... ON CONFLICT DO UPDATE para atomicidad.
        """
        # Intentar insertar con count=1
        stmt = (
            pg_insert(RateLimitBucket)
            .values(
                resource=resource,
                window_start=window_start,
                count=1,
            )
            .on_conflict_do_update(
                index_elements=["resource", "window_start"],
                set_={"count": RateLimitBucket.count + 1},
            )
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()

        # Retornar el count actual
        result = await self.db_session.execute(
            select(RateLimitBucket.count).where(
                RateLimitBucket.resource == resource,
                RateLimitBucket.window_start == window_start,
            )
        )
        return result.scalar_one()

    async def get_count(self, resource: str, window_start: datetime) -> int:
        """Retorna el count actual de un bucket."""
        result = await self.db_session.execute(
            select(RateLimitBucket.count).where(
                RateLimitBucket.resource == resource,
                RateLimitBucket.window_start == window_start,
            )
        )
        count = result.scalar_one_or_none()
        return count if count is not None else 0

    async def cleanup_old_windows(self, before: datetime) -> None:
        """Elimina buckets anteriores a la fecha dada."""
        stmt = delete(RateLimitBucket).where(RateLimitBucket.window_start < before)
        await self.db_session.execute(stmt)
        await self.db_session.commit()
