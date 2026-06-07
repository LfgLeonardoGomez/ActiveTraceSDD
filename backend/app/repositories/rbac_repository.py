"""Repositories para RBAC: Rol, Permiso, RolPermiso.

Todo query filtra por tenant_id (heredado de BaseRepository) y
excluye soft-deleted por defecto.
"""

from uuid import UUID

from sqlalchemy import select

from app.models.role import Permiso, Rol, RolPermiso
from app.repositories.base import BaseRepository


class RolRepository(BaseRepository[Rol]):
    """Repositorio de roles con scope de tenant."""

    def __init__(self, db_session, tenant_id: UUID) -> None:
        super().__init__(db_session, Rol, tenant_id)

    async def get_by_codigo(self, codigo: str) -> Rol | None:
        """Busca un rol por su código dentro del tenant."""
        query = self._base_query().where(Rol.codigo == codigo)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_tenant(self) -> list[Rol]:
        """Lista todos los roles del tenant no eliminados."""
        return await self.list()


class PermisoRepository(BaseRepository[Permiso]):
    """Repositorio de permisos con scope de tenant."""

    def __init__(self, db_session, tenant_id: UUID) -> None:
        super().__init__(db_session, Permiso, tenant_id)

    async def get_by_codigo(self, codigo: str) -> Permiso | None:
        """Busca un permiso por su código dentro del tenant."""
        query = self._base_query().where(Permiso.codigo == codigo)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_tenant(self) -> list[Permiso]:
        """Lista todos los permisos del tenant no eliminados."""
        return await self.list()


class RolPermisoRepository(BaseRepository[RolPermiso]):
    """Repositorio de asignaciones rol-permiso con resolución efectiva."""

    def __init__(self, db_session, tenant_id: UUID) -> None:
        super().__init__(db_session, RolPermiso, tenant_id)

    async def list_by_rol(self, rol_id: UUID) -> list[RolPermiso]:
        """Lista asignaciones activas de un rol."""
        query = self._base_query().where(RolPermiso.rol_id == rol_id)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def list_by_permiso(self, permiso_id: UUID) -> list[RolPermiso]:
        """Lista asignaciones activas de un permiso."""
        query = self._base_query().where(RolPermiso.permiso_id == permiso_id)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def get_permissions_for_roles(
        self, role_codes: list[str]
    ) -> set[tuple[str, bool]]:
        """Resuelve permisos efectivos como unión de roles dados.

        Args:
            role_codes: Lista de códigos de rol del usuario.

        Returns:
            Set de tuplas (permiso_codigo, es_propio).
        """
        if not role_codes:
            return set()

        query = (
            select(Permiso.codigo, RolPermiso.es_propio)
            .select_from(RolPermiso)
            .join(Rol, RolPermiso.rol_id == Rol.id)
            .join(Permiso, RolPermiso.permiso_id == Permiso.id)
            .where(
                Rol.tenant_id == self.tenant_id,
                Permiso.tenant_id == self.tenant_id,
                RolPermiso.tenant_id == self.tenant_id,
                Rol.codigo.in_(role_codes),
                Rol.deleted_at.is_(None),
                Permiso.deleted_at.is_(None),
                RolPermiso.deleted_at.is_(None),
            )
        )
        result = await self.db_session.execute(query)
        return set(result.all())
