"""Repositorio de umbrales de aprobación por asignación (C-10).

Todas las queries filtran por tenant_id.
upsert: crea o actualiza basado en la unique constraint (tenant_id, asignacion_id, materia_id).
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.umbral_materia import UmbralMateria
from app.repositories.base import BaseRepository


class UmbralRepository(BaseRepository[UmbralMateria]):
    """Repository de UmbralMateria con scope multi-tenant."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, UmbralMateria, tenant_id)

    async def get_by_asignacion(
        self,
        asignacion_id: UUID,
        materia_id: UUID,
    ) -> UmbralMateria | None:
        """Retorna el umbral activo para la asignación × materia, o None."""
        query = (
            select(UmbralMateria)
            .where(
                UmbralMateria.tenant_id == self.tenant_id,
                UmbralMateria.asignacion_id == asignacion_id,
                UmbralMateria.materia_id == materia_id,
                UmbralMateria.deleted_at.is_(None),
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        asignacion_id: UUID,
        materia_id: UUID,
        umbral_pct: int,
        valores_aprobatorios: list[str],
    ) -> UmbralMateria:
        """Crea o actualiza el umbral para la asignación × materia.

        Si ya existe, actualiza umbral_pct y valores_aprobatorios.
        Si no existe, crea un nuevo registro.
        """
        existing = await self.get_by_asignacion(asignacion_id, materia_id)

        if existing is not None:
            existing.umbral_pct = umbral_pct
            existing.valores_aprobatorios = valores_aprobatorios
            existing.updated_at = datetime.now(timezone.utc)
            await self.db_session.commit()
            await self.db_session.refresh(existing)
            return existing

        nuevo = UmbralMateria(
            tenant_id=self.tenant_id,
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios,
        )
        self.db_session.add(nuevo)
        await self.db_session.commit()
        await self.db_session.refresh(nuevo)
        return nuevo
