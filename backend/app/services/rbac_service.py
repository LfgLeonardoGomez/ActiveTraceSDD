"""Servicios de dominio para RBAC: Rol, Permiso, RolPermiso.

Clean Architecture: lógica de negocio orquesta repositories.
Validación de tenant en cada operación.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Permiso, Rol, RolPermiso
from app.repositories.rbac_repository import (
    PermisoRepository,
    RolPermisoRepository,
    RolRepository,
)


class RolService:
    """CRUD de roles con scope de tenant."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.repo = RolRepository(db_session, tenant_id)

    async def create(self, **kwargs) -> Rol:
        """Crea un nuevo rol en el tenant."""
        return await self.repo.create(**kwargs)

    async def get_by_id(self, rol_id: UUID) -> Rol | None:
        """Obtiene un rol por ID dentro del tenant."""
        return await self.repo.get_by_id(rol_id)

    async def get_by_codigo(self, codigo: str) -> Rol | None:
        """Obtiene un rol por código dentro del tenant."""
        return await self.repo.get_by_codigo(codigo)

    async def list(self) -> list[Rol]:
        """Lista roles activos del tenant."""
        return await self.repo.list_by_tenant()

    async def update(self, rol_id: UUID, data: dict) -> Rol | None:
        """Actualiza un rol existente."""
        return await self.repo.update(rol_id, data)

    async def delete(self, rol_id: UUID) -> bool:
        """Soft delete de un rol."""
        return await self.repo.delete(rol_id)


class PermisoService:
    """CRUD de permisos con scope de tenant."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.repo = PermisoRepository(db_session, tenant_id)

    async def create(self, **kwargs) -> Permiso:
        """Crea un nuevo permiso en el tenant."""
        return await self.repo.create(**kwargs)

    async def get_by_id(self, permiso_id: UUID) -> Permiso | None:
        """Obtiene un permiso por ID dentro del tenant."""
        return await self.repo.get_by_id(permiso_id)

    async def get_by_codigo(self, codigo: str) -> Permiso | None:
        """Obtiene un permiso por código dentro del tenant."""
        return await self.repo.get_by_codigo(codigo)

    async def list(self) -> list[Permiso]:
        """Lista permisos activos del tenant."""
        return await self.repo.list_by_tenant()

    async def update(self, permiso_id: UUID, data: dict) -> Permiso | None:
        """Actualiza un permiso existente."""
        return await self.repo.update(permiso_id, data)

    async def delete(self, permiso_id: UUID) -> bool:
        """Soft delete de un permiso."""
        return await self.repo.delete(permiso_id)


class RolPermisoService:
    """Asignar/quitar permisos a roles con validación de tenant."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.rp_repo = RolPermisoRepository(db_session, tenant_id)

    async def assign(self, rol_id: UUID, permiso_id: UUID, es_propio: bool = False) -> RolPermiso:
        """Asigna un permiso a un rol validando que ambos existan en el tenant."""
        rol_repo = RolRepository(self.db_session, self.tenant_id)
        perm_repo = PermisoRepository(self.db_session, self.tenant_id)

        rol = await rol_repo.get_by_id(rol_id)
        permiso = await perm_repo.get_by_id(permiso_id)

        if rol is None or permiso is None:
            raise ValueError("rol o permiso no existe en el tenant")

        return await self.rp_repo.create(
            rol_id=rol_id,
            permiso_id=permiso_id,
            es_propio=es_propio,
        )

    async def remove(self, rol_permiso_id: UUID) -> bool:
        """Quita una asignación (soft delete)."""
        return await self.rp_repo.delete(rol_permiso_id)

    async def list_by_rol(self, rol_id: UUID) -> list[RolPermiso]:
        """Lista asignaciones activas de un rol."""
        return await self.rp_repo.list_by_rol(rol_id)

    async def list_by_permiso(self, permiso_id: UUID) -> list[RolPermiso]:
        """Lista asignaciones activas de un permiso."""
        return await self.rp_repo.list_by_permiso(permiso_id)
