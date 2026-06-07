"""PermissionService: resolución de permisos efectivos.

Consume la matriz rol_permiso en cada request para evitar stale permissions.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.rbac_repository import RolPermisoRepository


class PermissionService:
    """Servicio de resolución de permisos efectivos."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id

    async def resolve_effective_permissions(
        self, role_codes: list[str]
    ) -> set[tuple[str, bool]]:
        """Resuelve permisos efectivos como unión de los roles dados.

        Args:
            role_codes: Códigos de rol del JWT del usuario autenticado.

        Returns:
            Conjunto de tuplas (permiso_codigo, es_propio).
        """
        repo = RolPermisoRepository(self.db_session, self.tenant_id)
        return await repo.get_permissions_for_roles(role_codes)
