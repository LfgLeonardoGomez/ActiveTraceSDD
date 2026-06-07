"""BaseRepository genérico con scope de tenant y soft delete.

Todo query es fail-closed: si no se provee tenant_id, lanza ValueError.
Filtro automático de soft delete (deleted_at IS NULL) salvo override
explícito vía `with_deleted()`.
"""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Repository genérico con scope de tenant obligatorio.

    Args:
        db_session: Sesión async de SQLAlchemy.
        model_class: Clase del modelo ORM.
        tenant_id: UUID del tenant obligatorio. None → ValueError.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        model_class: type[ModelType],
        tenant_id: UUID | None,
    ) -> None:
        if tenant_id is None:
            raise ValueError("tenant_id is required and cannot be None")
        if isinstance(tenant_id, str) and tenant_id == "":
            raise ValueError("tenant_id cannot be empty")
        self.db_session = db_session
        self.model_class = model_class
        self.tenant_id = tenant_id
        self._include_deleted = False

    def _base_query(self):
        """Construye el query base con filtro de tenant siempre presente."""
        query = select(self.model_class).where(
            self.model_class.tenant_id == self.tenant_id
        )
        if not self._include_deleted:
            query = query.where(self.model_class.deleted_at.is_(None))
        return query

    def with_deleted(self) -> "BaseRepository[ModelType]":
        """Devuelve una copia del repository que incluye registros eliminados."""
        cloned = BaseRepository(
            self.db_session,
            self.model_class,
            self.tenant_id,
        )
        cloned._include_deleted = True
        return cloned

    async def get_by_id(self, obj_id: UUID) -> ModelType | None:
        """Busca un registro por ID dentro del tenant scope.

        No devuelve registros soft-deleted a menos que `with_deleted()` se use.
        """
        query = self._base_query().where(self.model_class.id == obj_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list(self, **filters: Any) -> list[ModelType]:
        """Lista registros del tenant scope.

        Args:
            filters: kwargs adicionales de filtro (columna=valor).
        """
        query = self._base_query()
        for col, val in filters.items():
            if not hasattr(self.model_class, col):
                raise ValueError(f"Invalid filter column: {col}")
            query = query.where(getattr(self.model_class, col) == val)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ModelType:
        """Crea un registro asignando automáticamente tenant_id."""
        if "tenant_id" in kwargs:
            raise ValueError("tenant_id must not be passed explicitly; it is set by the repository")
        kwargs["tenant_id"] = self.tenant_id
        instance = self.model_class(**kwargs)
        self.db_session.add(instance)
        await self.db_session.commit()
        await self.db_session.refresh(instance)
        return instance

    async def update(self, obj_id: UUID, data: dict[str, Any]) -> ModelType | None:
        """Actualiza un registro si existe en el tenant scope.

        No actualiza registros soft-deleted.
        """
        query = self._base_query().where(self.model_class.id == obj_id)
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

    async def delete(self, obj_id: UUID) -> bool:
        """Soft delete: setea deleted_at en lugar de borrar físicamente.

        Returns:
            True si el registro fue encontrado y marcado como eliminado.
        """
        query = self._base_query().where(self.model_class.id == obj_id)
        result = await self.db_session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return False

        instance.deleted_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        return True
