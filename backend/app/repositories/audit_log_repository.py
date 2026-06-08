"""Repositorio de AuditLog — solo insert y query.

Sin métodos update ni delete: AuditLog es append-only.
La restricción también existe a nivel DB (trigger en migración 004).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    """Repositorio append-only para registros de auditoría.

    Siempre requiere tenant_id — no expone datos entre tenants.
    No subclasifica BaseRepository para dejar explícito que no hay update/delete.
    """

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        self.db_session = db_session
        self.tenant_id = tenant_id

    async def insert(self, entry: AuditLog) -> None:
        """Inserta un registro de auditoría en la sesión activa.

        Usa flush en lugar de commit para participar de la transacción del caller.
        """
        self.db_session.add(entry)
        await self.db_session.flush()

    async def list_by_tenant(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Lista registros de auditoría filtrados por tenant.

        Siempre scope a self.tenant_id — nunca cruza datos entre tenants.
        """
        query = (
            select(AuditLog)
            .where(AuditLog.tenant_id == self.tenant_id)
            .order_by(AuditLog.fecha_hora.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
