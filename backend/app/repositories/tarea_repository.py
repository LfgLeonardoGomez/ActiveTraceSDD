"""Repositorio de tareas y comentarios (C-16).

Todas las queries filtran por tenant_id (row-level isolation).
Lógica de negocio pertenece al Service.
"""

from datetime import datetime, timezone
from math import ceil
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tarea import ComentarioTarea, Tarea


class TareaRepository:
    """Repository de tareas: CRUD + filtering por tenant."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        self.db_session = db_session
        self.tenant_id = tenant_id

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _base_query(self):
        return select(Tarea).where(
            Tarea.tenant_id == self.tenant_id,
            Tarea.deleted_at.is_(None),
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create(self, data: dict) -> Tarea:
        tarea = Tarea(
            id=uuid4(),
            tenant_id=self.tenant_id,
            **data,
        )
        self.db_session.add(tarea)
        await self.db_session.commit()
        await self.db_session.refresh(tarea)
        return tarea

    async def get_by_id(self, tarea_id: UUID) -> Tarea | None:
        query = self._base_query().where(Tarea.id == tarea_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_por_tenant(
        self,
        page: int,
        page_size: int,
        estado: str | None = None,
        asignado_a: UUID | None = None,
        materia_id: UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[Tarea], int]:
        base = self._base_query()
        if estado is not None:
            base = base.where(Tarea.estado == estado)
        if asignado_a is not None:
            base = base.where(Tarea.asignado_a == asignado_a)
        if materia_id is not None:
            base = base.where(Tarea.materia_id == materia_id)
        if search is not None:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    Tarea.titulo.ilike(pattern),
                    Tarea.descripcion.ilike(pattern),
                )
            )

        total = (
            await self.db_session.execute(
                select(func.count()).select_from(base.subquery())
            )
        ).scalar_one()

        offset = (page - 1) * page_size
        rows_q = (
            base.order_by(Tarea.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(rows_q)
        items = list(result.scalars().all())
        return items, total

    async def list_por_asignado(
        self,
        asignado_a: UUID,
        page: int,
        page_size: int,
        estado: str | None = None,
    ) -> tuple[list[Tarea], int]:
        base = self._base_query().where(Tarea.asignado_a == asignado_a)
        if estado is not None:
            base = base.where(Tarea.estado == estado)

        total = (
            await self.db_session.execute(
                select(func.count()).select_from(base.subquery())
            )
        ).scalar_one()

        offset = (page - 1) * page_size
        rows_q = (
            base.order_by(Tarea.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(rows_q)
        items = list(result.scalars().all())
        return items, total

    async def update(self, tarea_id: UUID, data: dict) -> Tarea | None:
        tarea = await self.get_by_id(tarea_id)
        if tarea is None:
            return None
        for key, value in data.items():
            if hasattr(tarea, key):
                setattr(tarea, key, value)
        tarea.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(tarea)
        return tarea

    async def soft_delete(self, tarea_id: UUID) -> Tarea | None:
        tarea = await self.get_by_id(tarea_id)
        if tarea is None:
            return None
        tarea.deleted_at = datetime.now(timezone.utc)
        tarea.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(tarea)
        return tarea


class ComentarioTareaRepository:
    """Repository de comentarios de tarea."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        self.db_session = db_session
        self.tenant_id = tenant_id

    def _base_query(self):
        return select(ComentarioTarea).where(
            ComentarioTarea.tenant_id == self.tenant_id,
            ComentarioTarea.deleted_at.is_(None),
        )

    async def create(self, data: dict) -> ComentarioTarea:
        comentario = ComentarioTarea(
            id=uuid4(),
            tenant_id=self.tenant_id,
            **data,
        )
        self.db_session.add(comentario)
        await self.db_session.commit()
        await self.db_session.refresh(comentario)
        return comentario

    async def list_por_tarea(
        self,
        tarea_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[ComentarioTarea], int]:
        base = self._base_query().where(ComentarioTarea.tarea_id == tarea_id)

        total = (
            await self.db_session.execute(
                select(func.count()).select_from(base.subquery())
            )
        ).scalar_one()

        offset = (page - 1) * page_size
        rows_q = (
            base.order_by(ComentarioTarea.created_at.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(rows_q)
        items = list(result.scalars().all())
        return items, total

    async def soft_delete(self, comentario_id: UUID) -> ComentarioTarea | None:
        comentario = await self._get_by_id(comentario_id)
        if comentario is None:
            return None
        comentario.deleted_at = datetime.now(timezone.utc)
        comentario.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(comentario)
        return comentario

    async def _get_by_id(self, comentario_id: UUID) -> ComentarioTarea | None:
        query = self._base_query().where(ComentarioTarea.id == comentario_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
