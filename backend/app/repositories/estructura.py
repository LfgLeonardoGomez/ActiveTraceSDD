"""Repositorios para estructura académica (C-06): Carrera, Cohorte, Materia.

Todo query filtra por tenant_id (fail-closed) y excluye soft-deleted por defecto.
Hereda de BaseRepository para las operaciones comunes.
Métodos específicos usan queries SQLAlchemy explícitas (sin lazy-load).
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estructura import Carrera, Cohorte, Materia
from app.repositories.base import BaseRepository


class CarreraRepository(BaseRepository[Carrera]):
    """Repositorio de carreras con scope de tenant obligatorio."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, Carrera, tenant_id)

    async def get_by_id(self, obj_id: UUID) -> Carrera | None:
        """Busca carrera por ID dentro del tenant scope."""
        query = self._base_query().where(Carrera.id == obj_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        limit: int = 50,
        offset: int = 0,
        estado: str | None = None,
    ) -> tuple[list[Carrera], int]:
        """Lista carreras paginadas con filtro opcional por estado.

        Returns:
            Tuple (items, total_count).
        """
        base = self._base_query()
        if estado is not None:
            base = base.where(Carrera.estado == estado)

        count_query = select(func.count()).select_from(base.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = base.limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.scalars().all())

        return items, total

    async def exists_by_codigo(
        self, codigo: str, exclude_id: UUID | None = None
    ) -> bool:
        """Verifica si existe una carrera con el mismo código en el tenant.

        Args:
            codigo: Código a buscar.
            exclude_id: UUID a excluir (para updates — no contar el propio registro).
        """
        query = self._base_query().where(Carrera.codigo == codigo)
        if exclude_id is not None:
            query = query.where(Carrera.id != exclude_id)
        result = await self.db_session.execute(select(func.count()).select_from(query.subquery()))
        return result.scalar_one() > 0

    async def soft_delete(self, obj_id: UUID) -> bool:
        """Soft delete de carrera: setea deleted_at."""
        query = self._base_query().where(Carrera.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return False
        instance.deleted_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        return True

    async def update(self, obj_id: UUID, data: dict[str, Any]) -> Carrera | None:
        """Actualiza campos de una carrera."""
        query = self._base_query().where(Carrera.id == obj_id)
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


class CohorteRepository(BaseRepository[Cohorte]):
    """Repositorio de cohortes con scope de tenant obligatorio."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, Cohorte, tenant_id)

    async def get_by_id(self, obj_id: UUID) -> Cohorte | None:
        """Busca cohorte por ID dentro del tenant scope."""
        query = self._base_query().where(Cohorte.id == obj_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        limit: int = 50,
        offset: int = 0,
        estado: str | None = None,
        carrera_id: UUID | None = None,
    ) -> tuple[list[Cohorte], int]:
        """Lista cohortes paginadas con filtros opcionales.

        Returns:
            Tuple (items, total_count).
        """
        base = self._base_query()
        if estado is not None:
            base = base.where(Cohorte.estado == estado)
        if carrera_id is not None:
            base = base.where(Cohorte.carrera_id == carrera_id)

        count_query = select(func.count()).select_from(base.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = base.limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.scalars().all())

        return items, total

    async def exists_by_nombre_en_carrera(
        self,
        carrera_id: UUID,
        nombre: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """Verifica unicidad (tenant_id, carrera_id, nombre)."""
        query = (
            self._base_query()
            .where(Cohorte.carrera_id == carrera_id)
            .where(Cohorte.nombre == nombre)
        )
        if exclude_id is not None:
            query = query.where(Cohorte.id != exclude_id)
        result = await self.db_session.execute(select(func.count()).select_from(query.subquery()))
        return result.scalar_one() > 0

    async def count_activas_por_carrera(self, carrera_id: UUID) -> int:
        """Cuenta cohortes en estado Activa para una carrera dada."""
        query = (
            self._base_query()
            .where(Cohorte.carrera_id == carrera_id)
            .where(Cohorte.estado == "Activa")
        )
        result = await self.db_session.execute(select(func.count()).select_from(query.subquery()))
        return result.scalar_one()

    async def soft_delete(self, obj_id: UUID) -> bool:
        """Soft delete de cohorte: setea deleted_at."""
        query = self._base_query().where(Cohorte.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return False
        instance.deleted_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        return True

    async def update(self, obj_id: UUID, data: dict[str, Any]) -> Cohorte | None:
        """Actualiza campos de una cohorte."""
        query = self._base_query().where(Cohorte.id == obj_id)
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


class MateriaRepository(BaseRepository[Materia]):
    """Repositorio de materias con scope de tenant obligatorio."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, Materia, tenant_id)

    async def get_by_id(self, obj_id: UUID) -> Materia | None:
        """Busca materia por ID dentro del tenant scope."""
        query = self._base_query().where(Materia.id == obj_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        limit: int = 50,
        offset: int = 0,
        estado: str | None = None,
    ) -> tuple[list[Materia], int]:
        """Lista materias paginadas con filtro opcional por estado.

        Returns:
            Tuple (items, total_count).
        """
        base = self._base_query()
        if estado is not None:
            base = base.where(Materia.estado == estado)

        count_query = select(func.count()).select_from(base.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = base.limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.scalars().all())

        return items, total

    async def exists_by_codigo(
        self, codigo: str, exclude_id: UUID | None = None
    ) -> bool:
        """Verifica si existe una materia con el mismo código en el tenant."""
        query = self._base_query().where(Materia.codigo == codigo)
        if exclude_id is not None:
            query = query.where(Materia.id != exclude_id)
        result = await self.db_session.execute(select(func.count()).select_from(query.subquery()))
        return result.scalar_one() > 0

    async def soft_delete(self, obj_id: UUID) -> bool:
        """Soft delete de materia: setea deleted_at."""
        query = self._base_query().where(Materia.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return False
        instance.deleted_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        return True

    async def update(self, obj_id: UUID, data: dict[str, Any]) -> Materia | None:
        """Actualiza campos de una materia."""
        query = self._base_query().where(Materia.id == obj_id)
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
