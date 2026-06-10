"""Repositorio de Asignacion con scope de tenant obligatorio (C-07).

Implementa CRUD con filtros para listado: usuario_id, rol, materia_id,
carrera_id, cohorte_id, incluir_vencidas (basado en fechas), incluir_eliminadas.

Nota: incluir_vencidas no filtra en DB por estado_vigencia (que es @property),
sino que incluye todas las asignaciones (vigentes y vencidas según fechas).
"""

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.repositories.base import BaseRepository


class AsignacionRepository(BaseRepository[Asignacion]):
    """Repositorio de asignaciones con scope de tenant obligatorio.

    Por defecto excluye registros soft-deleted. Todas las consultas
    filtran automáticamente por tenant_id.
    """

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, Asignacion, tenant_id)

    async def create(self, **kwargs: Any) -> Asignacion:
        """Crea una asignación asignando automáticamente tenant_id."""
        if "tenant_id" in kwargs:
            raise ValueError("tenant_id must not be passed explicitly")
        kwargs["tenant_id"] = self.tenant_id

        instance = Asignacion(**kwargs)
        self.db_session.add(instance)
        await self.db_session.commit()
        await self.db_session.refresh(instance)
        return instance

    async def get_by_id(self, obj_id: UUID) -> Asignacion | None:
        """Busca asignación por ID dentro del tenant scope."""
        query = self._base_query().where(Asignacion.id == obj_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        limit: int = 50,
        offset: int = 0,
        usuario_id: UUID | None = None,
        rol: str | None = None,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        incluir_vencidas: bool = True,
        incluir_eliminadas: bool = False,
    ) -> tuple[list[Asignacion], int]:
        """Lista asignaciones del tenant con filtros opcionales.

        Args:
            limit: Máximo de registros por página.
            offset: Saltar N registros.
            usuario_id: Filtrar por usuario específico.
            rol: Filtrar por rol.
            materia_id: Filtrar por materia.
            carrera_id: Filtrar por carrera.
            cohorte_id: Filtrar por cohorte.
            incluir_vencidas: Si True, incluye asignaciones con hasta < today.
                              (El filtrado por vigencia se hace en el @property
                              del modelo, no en DB para no duplicar lógica.)
            incluir_eliminadas: Si True, incluye registros soft-deleted.

        Returns:
            Tuple (items, total_count).
        """
        # Base query con filtro de tenant y soft-delete
        if incluir_eliminadas:
            base = select(Asignacion).where(Asignacion.tenant_id == self.tenant_id)
        else:
            base = self._base_query()

        # Filtros opcionales
        if usuario_id is not None:
            base = base.where(Asignacion.usuario_id == usuario_id)
        if rol is not None:
            base = base.where(Asignacion.rol == rol)
        if materia_id is not None:
            base = base.where(Asignacion.materia_id == materia_id)
        if carrera_id is not None:
            base = base.where(Asignacion.carrera_id == carrera_id)
        if cohorte_id is not None:
            base = base.where(Asignacion.cohorte_id == cohorte_id)

        # Filtro de vigencia en DB (si incluir_vencidas=False, excluir las con hasta < today)
        if not incluir_vencidas:
            today = date.today()
            base = base.where(
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= today)
            ).where(Asignacion.desde <= today)

        count_query = select(func.count()).select_from(base.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = base.limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.scalars().all())

        return items, total

    async def update(self, obj_id: UUID, data: dict[str, Any]) -> Asignacion | None:
        """Actualiza campos de una asignación.

        Returns:
            Asignación actualizada, o None si no existe en el tenant.
        """
        query = self._base_query().where(Asignacion.id == obj_id)
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

    async def soft_delete(self, obj_id: UUID) -> bool:
        """Soft delete: setea deleted_at.

        Returns:
            True si fue encontrado y marcado como eliminado.
        """
        query = self._base_query().where(Asignacion.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return False

        instance.deleted_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        return True
