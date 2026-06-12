"""Repositorio de panel de auditoría — agregaciones SELECT-only (C-19).

Solo métodos de lectura: get_* y list_*.
NUNCA insert, update, delete, add, flush — AuditLog es inmutable.
Todos los queries filtran por tenant_id (row-level isolation).
Agregaciones GROUP BY on-the-fly en SQL, no en Python (D5).
"""

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import Date, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.comunicacion import Comunicacion
from app.models.user import Usuario


class AuditoriaPanelRepository:
    """Repository de panel — solo lectura sobre audit_log y comunicacion.

    Siempre requiere tenant_id para aislar datos entre tenants.
    No subclasifica BaseRepository para dejar explícito que no hay update/delete.
    """

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        self.db_session = db_session
        self.tenant_id = tenant_id

    # ------------------------------------------------------------------
    # 2.2 acciones_por_dia
    # ------------------------------------------------------------------

    async def get_acciones_por_dia(
        self,
        fecha_desde: datetime,
        fecha_hasta: datetime,
        materia_id: UUID | None = None,
        actor_filter: UUID | None = None,
    ) -> list[tuple[date, int]]:
        """Cuenta acciones de auditoría agrupadas por día UTC.

        Retorna lista de tuplas (fecha, total) ordenadas ASC.
        """
        conditions = [
            AuditLog.tenant_id == self.tenant_id,
            AuditLog.fecha_hora >= fecha_desde,
            AuditLog.fecha_hora <= fecha_hasta,
        ]
        if materia_id is not None:
            conditions.append(AuditLog.materia_id == materia_id)
        if actor_filter is not None:
            conditions.append(
                or_(
                    AuditLog.actor_id == actor_filter,
                    AuditLog.impersonado_id == actor_filter,
                )
            )

        # PostgreSQL: CAST(timezone('UTC', fecha_hora) AS DATE)
        fecha_col = func.cast(
            func.timezone("UTC", AuditLog.fecha_hora),
            Date,
        )

        query = (
            select(
                fecha_col.label("fecha"),
                func.count(AuditLog.id).label("total"),
            )
            .where(*conditions)
            .group_by(fecha_col)
            .order_by(fecha_col.asc())
        )
        result = await self.db_session.execute(query)
        return [(row.fecha, row.total) for row in result.all()]

    # ------------------------------------------------------------------
    # 2.3 comunicaciones_por_docente
    # ------------------------------------------------------------------

    async def get_comunicaciones_por_docente(
        self,
        fecha_desde: datetime,
        fecha_hasta: datetime,
        materia_id: UUID | None = None,
        actor_filter: UUID | None = None,
    ) -> list[dict]:
        """Agrega comunicaciones por (actor_id, estado) con nombre del usuario.

        Retorna lista de dicts con campos: actor_id, usuario_nombre, estado, conteo.
        """
        conditions = [
            Comunicacion.tenant_id == self.tenant_id,
            Comunicacion.deleted_at.is_(None),
            Comunicacion.created_at >= fecha_desde,
            Comunicacion.created_at <= fecha_hasta,
        ]
        if materia_id is not None:
            conditions.append(Comunicacion.materia_id == materia_id)
        if actor_filter is not None:
            conditions.append(Comunicacion.enviado_por == actor_filter)

        query = (
            select(
                Comunicacion.enviado_por.label("actor_id"),
                Usuario.nombre.label("usuario_nombre"),
                Comunicacion.estado.label("estado"),
                func.count(Comunicacion.id).label("conteo"),
            )
            .join(
                Usuario,
                Usuario.id == Comunicacion.enviado_por,
            )
            .where(*conditions)
            .group_by(
                Comunicacion.enviado_por,
                Usuario.nombre,
                Comunicacion.estado,
            )
        )
        result = await self.db_session.execute(query)
        return [row._asdict() for row in result.all()]

    # ------------------------------------------------------------------
    # 2.4 interacciones_por_docente_materia
    # ------------------------------------------------------------------

    async def get_interacciones_por_docente_materia(
        self,
        fecha_desde: datetime,
        fecha_hasta: datetime,
        materia_id: UUID | None = None,
        usuario_id: UUID | None = None,
        actor_filter: UUID | None = None,
    ) -> list[dict]:
        """Agrega interacciones por (actor_id, materia_id, accion) con JOINs.

        materia_id puede ser NULL (LEFT JOIN con Materia).
        Retorna lista de dicts con: actor_id, actor_nombre, materia_id,
        materia_nombre, accion, total.
        """
        from app.models.estructura import Materia

        conditions = [
            AuditLog.tenant_id == self.tenant_id,
            AuditLog.fecha_hora >= fecha_desde,
            AuditLog.fecha_hora <= fecha_hasta,
        ]
        if materia_id is not None:
            conditions.append(AuditLog.materia_id == materia_id)
        if usuario_id is not None:
            conditions.append(
                or_(
                    AuditLog.actor_id == usuario_id,
                    AuditLog.impersonado_id == usuario_id,
                )
            )
        if actor_filter is not None:
            conditions.append(
                or_(
                    AuditLog.actor_id == actor_filter,
                    AuditLog.impersonado_id == actor_filter,
                )
            )

        query = (
            select(
                AuditLog.actor_id.label("actor_id"),
                Usuario.nombre.label("actor_nombre"),
                AuditLog.materia_id.label("materia_id"),
                Materia.nombre.label("materia_nombre"),
                AuditLog.accion.label("accion"),
                func.count(AuditLog.id).label("total"),
            )
            .join(Usuario, Usuario.id == AuditLog.actor_id)
            .outerjoin(
                Materia,
                (Materia.id == AuditLog.materia_id)
                & (Materia.tenant_id == self.tenant_id),
            )
            .where(*conditions)
            .group_by(
                AuditLog.actor_id,
                Usuario.nombre,
                AuditLog.materia_id,
                Materia.nombre,
                AuditLog.accion,
            )
        )
        result = await self.db_session.execute(query)
        return [row._asdict() for row in result.all()]

    # ------------------------------------------------------------------
    # 2.5 ultimas_acciones
    # ------------------------------------------------------------------

    async def get_ultimas_acciones(
        self,
        limit: int = 200,
        materia_id: UUID | None = None,
        usuario_id: UUID | None = None,
        accion: str | None = None,
        actor_filter: UUID | None = None,
    ) -> list[AuditLog]:
        """Lista las últimas N acciones de auditoría ordenadas DESC.

        Sin paginación — el límite está acotado en el Service (max 1000).
        """
        conditions = [AuditLog.tenant_id == self.tenant_id]
        if materia_id is not None:
            conditions.append(AuditLog.materia_id == materia_id)
        if usuario_id is not None:
            conditions.append(
                or_(
                    AuditLog.actor_id == usuario_id,
                    AuditLog.impersonado_id == usuario_id,
                )
            )
        if accion is not None:
            conditions.append(AuditLog.accion == str(accion))
        if actor_filter is not None:
            conditions.append(
                or_(
                    AuditLog.actor_id == actor_filter,
                    AuditLog.impersonado_id == actor_filter,
                )
            )

        query = (
            select(AuditLog)
            .where(*conditions)
            .order_by(AuditLog.fecha_hora.desc())
            .limit(limit)
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
