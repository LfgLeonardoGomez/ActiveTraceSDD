"""Repositorio de Guardia (C-13).

Operaciones de guardias con scope de tenant, JOINs enriquecidos y exportación.
"""

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estructura import Carrera, Cohorte, Materia
from app.models.guardia import Guardia
from app.models.user import Usuario
from app.repositories.base import BaseRepository


class GuardiaRepository(BaseRepository[Guardia]):
    """Repositorio de guardias con scope de tenant."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, Guardia, tenant_id)

    def _base_join_query(self):
        """Query base con JOINs a Usuario, Materia, Carrera, Cohorte.

        Siempre filtra por tenant_id y deleted_at IS NULL en todas las tablas.
        """
        return (
            select(
                Guardia,
                Usuario.nombre.label("tutor_nombre"),
                Usuario.apellidos.label("tutor_apellidos"),
                Materia.nombre.label("materia_nombre"),
                Carrera.nombre.label("carrera_nombre"),
                Cohorte.nombre.label("cohorte_nombre"),
            )
            .join(Usuario, Guardia.tutor_id == Usuario.id)
            .join(Materia, Guardia.materia_id == Materia.id)
            .join(Carrera, Guardia.carrera_id == Carrera.id)
            .join(Cohorte, Guardia.cohorte_id == Cohorte.id)
            .where(Guardia.tenant_id == self.tenant_id)
            .where(Guardia.deleted_at.is_(None))
            .where(Usuario.deleted_at.is_(None))
            .where(Materia.deleted_at.is_(None))
            .where(Carrera.deleted_at.is_(None))
            .where(Cohorte.deleted_at.is_(None))
        )

    async def list_guardias(
        self,
        materia_id: UUID | None = None,
        tutor_id: UUID | None = None,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[Any, ...]], int]:
        """Lista guardias paginadas con nombres enriquecidos.

        Returns:
            Tuple (lista de tuplas (Guardia, ...nombres), total_count).
        """
        query = self._base_join_query()
        if materia_id is not None:
            query = query.where(Guardia.materia_id == materia_id)
        if tutor_id is not None:
            query = query.where(Guardia.tutor_id == tutor_id)
        if estado is not None:
            query = query.where(Guardia.estado == estado)
        if fecha_desde is not None:
            query = query.where(Guardia.fecha >= fecha_desde)
        if fecha_hasta is not None:
            query = query.where(Guardia.fecha <= fecha_hasta)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = query.limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.all())

        return items, total

    async def get_guardias_for_export(
        self,
        materia_id: UUID | None = None,
        tutor_id: UUID | None = None,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[tuple[Any, ...]]:
        """Devuelve todas las guardias con nombres enriquecidos para exportación.

        No pagina; aplica los mismos filtros que list_guardias.
        """
        query = self._base_join_query()
        if materia_id is not None:
            query = query.where(Guardia.materia_id == materia_id)
        if tutor_id is not None:
            query = query.where(Guardia.tutor_id == tutor_id)
        if estado is not None:
            query = query.where(Guardia.estado == estado)
        if fecha_desde is not None:
            query = query.where(Guardia.fecha >= fecha_desde)
        if fecha_hasta is not None:
            query = query.where(Guardia.fecha <= fecha_hasta)

        result = await self.db_session.execute(query)
        return list(result.all())
