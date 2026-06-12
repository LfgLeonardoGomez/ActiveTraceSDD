"""Service de consulta del log completo de auditoría (C-19).

Orquesta filtros, scope (propio) y paginación.
Flujo: Router → Service → Repository (unidireccional).
"""

import math
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.auditoria_log_query_repository import AuditoriaLogQueryRepository
from app.schemas.auditoria import AuditLogEntrySchema, AuditLogPageResponse
from app.schemas.rbac_schema import PermissionContext
from app.services.auditoria_panel_service import AuditoriaPanelService


class AuditoriaLogQueryService:
    """Service de consulta paginada del log de auditoría (F9.2, RN-23/RN-24).

    Resuelve scope (propio) y delega la paginación al repository.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        tenant_id: UUID,
        current_user_id: UUID,
    ) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self._repo = AuditoriaLogQueryRepository(db_session, tenant_id)

    def _resolve_actor_filter(self, permission_ctx: PermissionContext) -> UUID | None:
        """Retorna el UUID del usuario actual si is_propio, sino None."""
        return self.current_user_id if permission_ctx.is_propio else None

    async def list_log(
        self,
        filtros: dict,
        permission_ctx: PermissionContext,
        page: int,
        page_size: int,
    ) -> AuditLogPageResponse:
        """Retorna el log de auditoría paginado con filtros.

        page_size máximo: 200 (validado en el Router con Query(le=200)).
        """
        actor_filter = self._resolve_actor_filter(permission_ctx)

        items_orm, total = await self._repo.list_paginated(
            filtros=filtros,
            actor_filter=actor_filter,
            page=page,
            page_size=page_size,
        )

        pages = math.ceil(total / page_size) if page_size > 0 and total > 0 else 0

        items = [
            AuditLogEntrySchema(
                id=entry.id,
                fecha_hora=entry.fecha_hora,
                actor_id=entry.actor_id,
                impersonado_id=entry.impersonado_id,
                materia_id=entry.materia_id,
                accion=entry.accion,
                categoria=AuditoriaPanelService.categoria_for(entry.accion),
                filas_afectadas=entry.filas_afectadas,
                ip=entry.ip,
                user_agent=entry.user_agent,
                detalle=entry.detalle,
            )
            for entry in items_orm
        ]

        return AuditLogPageResponse(
            items=items,
            total=total,
            page=page,
            pages=pages,
        )
