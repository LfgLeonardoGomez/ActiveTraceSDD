"""Repositorio de consulta del log de auditoría — paginado + filtros (C-19).

Solo lectura: solo métodos list_* y get_*.
NUNCA insert, update, delete, add, flush.
Todos los queries filtran por tenant_id (row-level isolation).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select, type_coerce
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditoriaLogQueryRepository:
    """Repository de consulta paginada del log completo de auditoría.

    Solo lectura. Sin métodos de escritura — AuditLog es inmutable.
    Requiere tenant_id para aislamiento multi-tenant.
    """

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        self.db_session = db_session
        self.tenant_id = tenant_id

    async def list_paginated(
        self,
        filtros: dict,
        actor_filter: UUID | None,
        page: int,
        page_size: int,
    ) -> tuple[list[AuditLog], int]:
        """Lista paginada del log de auditoría con filtros.

        Filtros aceptados (todos opcionales):
          fecha_desde: datetime — límite inferior de fecha_hora (inclusive)
          fecha_hasta: datetime — límite superior de fecha_hora (inclusive)
          materia_id: UUID
          usuario_id: UUID — matchea actor_id OR impersonado_id
          accion: str — código exacto de AuditAction
          estado: str — filtra `detalle ->> 'estado'` cuando presente

        actor_filter: UUID | None — scope (propio) del COORDINADOR.
          Si no es None, agrega (actor_id = :af OR impersonado_id = :af).

        Retorna (items, total).
        """
        conditions = [AuditLog.tenant_id == self.tenant_id]

        fecha_desde = filtros.get("fecha_desde")
        if fecha_desde is not None:
            conditions.append(AuditLog.fecha_hora >= fecha_desde)

        fecha_hasta = filtros.get("fecha_hasta")
        if fecha_hasta is not None:
            conditions.append(AuditLog.fecha_hora <= fecha_hasta)

        materia_id = filtros.get("materia_id")
        if materia_id is not None:
            conditions.append(AuditLog.materia_id == materia_id)

        usuario_id = filtros.get("usuario_id")
        if usuario_id is not None:
            conditions.append(
                or_(
                    AuditLog.actor_id == usuario_id,
                    AuditLog.impersonado_id == usuario_id,
                )
            )

        accion = filtros.get("accion")
        if accion is not None:
            conditions.append(AuditLog.accion == str(accion))

        estado = filtros.get("estado")
        if estado is not None:
            # Filtra sobre detalle JSONB: detalle ->> 'estado' = :estado
            conditions.append(
                AuditLog.detalle["estado"].as_string() == estado
            )

        # Scope (propio) del COORDINADOR — siempre encima de todos los otros filtros
        if actor_filter is not None:
            conditions.append(
                or_(
                    AuditLog.actor_id == actor_filter,
                    AuditLog.impersonado_id == actor_filter,
                )
            )

        base_stmt = select(AuditLog).where(*conditions)

        # Count total (query separada con mismos WHEREs)
        count_stmt = select(func.count()).select_from(
            select(AuditLog.id).where(*conditions).subquery()
        )
        total = (await self.db_session.execute(count_stmt)).scalar_one()

        # Datos paginados
        offset = (page - 1) * page_size
        items_stmt = (
            base_stmt
            .order_by(AuditLog.fecha_hora.desc())
            .limit(page_size)
            .offset(offset)
        )
        result = await self.db_session.execute(items_stmt)
        items = list(result.scalars().all())

        return items, total
