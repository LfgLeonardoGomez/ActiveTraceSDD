"""Repositorios para programas y fechas académicas (C-17).

Todo query filtra por tenant_id (fail-closed) y excluye soft-deleted por defecto.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.programa_materia import FechaAcademica, ProgramaMateria
from app.repositories.base import BaseRepository


class ProgramaMateriaRepository(BaseRepository[ProgramaMateria]):
    """Repositorio de programas de materia con scope de tenant obligatorio."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, ProgramaMateria, tenant_id)

    async def get_by_id(self, obj_id: UUID) -> ProgramaMateria | None:
        """Busca programa por ID dentro del tenant scope."""
        query = self._base_query().where(ProgramaMateria.id == obj_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_materia(
        self, materia_id: UUID, limit: int = 50, offset: int = 0
    ) -> tuple[list[ProgramaMateria], int]:
        """Lista programas por materia paginados.

        Returns:
            Tuple (items, total_count).
        """
        base = self._base_query().where(ProgramaMateria.materia_id == materia_id)

        count_query = select(func.count()).select_from(base.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = base.limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.scalars().all())

        return items, total

    async def count_by_combinacion(
        self,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_id: UUID,
        exclude_id: UUID | None = None,
    ) -> int:
        """Cuenta programas para la combinación materia×carrera×cohorte.

        Args:
            exclude_id: UUID a excluir (para updates).
        """
        query = (
            self._base_query()
            .where(ProgramaMateria.materia_id == materia_id)
            .where(ProgramaMateria.carrera_id == carrera_id)
            .where(ProgramaMateria.cohorte_id == cohorte_id)
        )
        if exclude_id is not None:
            query = query.where(ProgramaMateria.id != exclude_id)
        result = await self.db_session.execute(
            select(func.count()).select_from(query.subquery())
        )
        return result.scalar_one()

    async def soft_delete(self, obj_id: UUID) -> bool:
        """Soft delete de programa: setea deleted_at."""
        query = self._base_query().where(ProgramaMateria.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return False
        instance.deleted_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        return True

    async def update(self, obj_id: UUID, data: dict[str, Any]) -> ProgramaMateria | None:
        """Actualiza campos de un programa."""
        query = self._base_query().where(ProgramaMateria.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(instance)
        return instance


class FechaAcademicaRepository(BaseRepository[FechaAcademica]):
    """Repositorio de fechas académicas con scope de tenant obligatorio."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, FechaAcademica, tenant_id)

    async def get_by_id(self, obj_id: UUID) -> FechaAcademica | None:
        """Busca fecha por ID dentro del tenant scope."""
        query = self._base_query().where(FechaAcademica.id == obj_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_materia(
        self, materia_id: UUID, limit: int = 50, offset: int = 0
    ) -> tuple[list[FechaAcademica], int]:
        """Lista fechas por materia paginadas.

        Returns:
            Tuple (items, total_count).
        """
        base = self._base_query().where(FechaAcademica.materia_id == materia_id)

        count_query = select(func.count()).select_from(base.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = base.order_by(
            FechaAcademica.tipo, FechaAcademica.numero, FechaAcademica.fecha
        ).limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.scalars().all())

        return items, total

    async def list_by_materia_cohorte(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[FechaAcademica], int]:
        """Lista fechas por materia y cohorte paginadas.

        Returns:
            Tuple (items, total_count).
        """
        base = (
            self._base_query()
            .where(FechaAcademica.materia_id == materia_id)
            .where(FechaAcademica.cohorte_id == cohorte_id)
        )

        count_query = select(func.count()).select_from(base.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = base.order_by(
            FechaAcademica.tipo, FechaAcademica.numero, FechaAcademica.fecha
        ).limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.scalars().all())

        return items, total

    async def soft_delete(self, obj_id: UUID) -> bool:
        """Soft delete de fecha: setea deleted_at."""
        query = self._base_query().where(FechaAcademica.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return False
        instance.deleted_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        return True

    async def update(self, obj_id: UUID, data: dict[str, Any]) -> FechaAcademica | None:
        """Actualiza campos de una fecha académica."""
        query = self._base_query().where(FechaAcademica.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(instance)
        return instance
