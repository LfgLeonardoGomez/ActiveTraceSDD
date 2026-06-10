"""Repositorios de SlotEncuentro e InstanciaEncuentro (C-13).

Operaciones de encuentros con scope de tenant y soft delete.
- SlotEncuentroRepository: CRUD de slots + listado paginado
- InstanciaEncuentroRepository: CRUD de instancias + listado paginado + soft delete por slot
"""

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro
from app.repositories.base import BaseRepository


class SlotEncuentroRepository(BaseRepository[SlotEncuentro]):
    """Repositorio de slots de encuentro."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, SlotEncuentro, tenant_id)

    async def list_slots(
        self,
        materia_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SlotEncuentro], int]:
        """Lista slots paginados con filtro opcional por materia."""
        query = self._base_query()
        if materia_id is not None:
            query = query.where(SlotEncuentro.materia_id == materia_id)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = query.limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.scalars().all())

        return items, total

    async def bulk_create_instancias(
        self,
        instances: list[InstanciaEncuentro],
    ) -> None:
        """Inserta múltiples instancias en la sesión activa (flush, no commit).

        El caller debe hacer commit para persistir.
        """
        self.db_session.add_all(instances)
        await self.db_session.flush()


class InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro]):
    """Repositorio de instancias de encuentro."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, InstanciaEncuentro, tenant_id)

    async def list_instancias(
        self,
        materia_id: UUID | None = None,
        slot_id: UUID | None = None,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[InstanciaEncuentro], int]:
        """Lista instancias paginadas con filtros."""
        query = self._base_query()
        if materia_id is not None:
            query = query.where(InstanciaEncuentro.materia_id == materia_id)
        if slot_id is not None:
            query = query.where(InstanciaEncuentro.slot_id == slot_id)
        if estado is not None:
            query = query.where(InstanciaEncuentro.estado == estado)
        if fecha_desde is not None:
            query = query.where(InstanciaEncuentro.fecha >= fecha_desde)
        if fecha_hasta is not None:
            query = query.where(InstanciaEncuentro.fecha <= fecha_hasta)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = query.limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.scalars().all())

        return items, total

    async def update_instancia(
        self,
        instancia_id: UUID,
        data: dict[str, Any],
    ) -> InstanciaEncuentro | None:
        """Actualiza una instancia si existe en el tenant scope."""
        query = self._base_query().where(InstanciaEncuentro.id == instancia_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None

        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        return instance

    async def soft_delete_by_slot_id(self, slot_id: UUID) -> int:
        """Soft-delete de todas las instancias asociadas a un slot.

        Returns:
            Cantidad de instancias afectadas.
        """
        from datetime import datetime, timezone

        stmt = (
            update(InstanciaEncuentro)
            .where(InstanciaEncuentro.tenant_id == self.tenant_id)
            .where(InstanciaEncuentro.deleted_at.is_(None))
            .where(InstanciaEncuentro.slot_id == slot_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self.db_session.execute(stmt)
        return result.rowcount
