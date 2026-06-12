"""Service del panel de auditoría y métricas (C-19).

Orquesta filtros, aplica scope (propio), deriva categorías.
Flujo: Router → Service → Repository (unidireccional).
Sin acceso directo a DB — siempre vía repository.
"""

import math
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction
from app.repositories.auditoria_panel_repository import AuditoriaPanelRepository
from app.schemas.auditoria import (
    AccionesPorDiaItem,
    AccionesPorDiaResponse,
    CatalogoAccionItem,
    CatalogoAccionesResponse,
    ComunicacionesPorDocenteItem,
    ComunicacionesPorDocenteResponse,
    ConteoEstadosComunicacion,
    InteraccionesPorDocenteMateriaItem,
    InteraccionesPorDocenteMateriaResponse,
    RangoFechasResponse,
    UltimaAccionItem,
    UltimasAccionesResponse,
)
from app.schemas.rbac_schema import PermissionContext


class AuditoriaPanelService:
    """Orquesta el panel de auditoría y métricas (F9.1).

    Resuelve scope, rango de fechas y categorías antes de delegar al repository.
    """

    _DEFAULT_LIMIT = 200
    _MAX_LIMIT = 1000
    _DEFAULT_RANGO_DIAS = 30

    def __init__(
        self,
        db_session: AsyncSession,
        tenant_id: UUID,
        current_user_id: UUID,
    ) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self._repo = AuditoriaPanelRepository(db_session, tenant_id)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _resolve_actor_filter(self, permission_ctx: PermissionContext) -> UUID | None:
        """Retorna el UUID del usuario actual si is_propio, sino None."""
        return self.current_user_id if permission_ctx.is_propio else None

    def _resolve_rango(
        self,
        fecha_desde: date | datetime | None,
        fecha_hasta: date | datetime | None,
    ) -> tuple[datetime, datetime]:
        """Convierte date/datetime a datetime UTC con rango completo.

        Reglas (D3 del design):
          - ambos None → últimos 30 días
          - solo fecha_desde → hasta = now()
          - solo fecha_hasta → desde = fecha_hasta - 30 días
          - ambos → tal como vienen
        """
        now = datetime.now(timezone.utc)

        def _to_dt_start(d: date | datetime) -> datetime:
            if isinstance(d, datetime):
                return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
            return datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc)

        def _to_dt_end(d: date | datetime) -> datetime:
            if isinstance(d, datetime):
                return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
            return datetime(d.year, d.month, d.day, 23, 59, 59, 999999, tzinfo=timezone.utc)

        if fecha_desde is None and fecha_hasta is None:
            return now - timedelta(days=self._DEFAULT_RANGO_DIAS), now
        if fecha_desde is None:
            fh = _to_dt_end(fecha_hasta)
            return fh - timedelta(days=self._DEFAULT_RANGO_DIAS), fh
        if fecha_hasta is None:
            return _to_dt_start(fecha_desde), now
        return _to_dt_start(fecha_desde), _to_dt_end(fecha_hasta)

    @staticmethod
    def categoria_for(accion: str) -> str:
        """Deriva la categoría del código de acción por su prefijo.

        Ejemplo: 'CALIFICACIONES_IMPORTAR' → 'CALIFICACIONES'
        Pure function — sin acceso a BD.
        """
        return accion.split("_", 1)[0]

    # ------------------------------------------------------------------
    # 4.5 get_acciones_por_dia
    # ------------------------------------------------------------------

    async def get_acciones_por_dia(
        self,
        filtros: dict,
        permission_ctx: PermissionContext,
    ) -> AccionesPorDiaResponse:
        """Retorna el conteo de acciones de auditoría agrupadas por día."""
        fd, fh = self._resolve_rango(
            filtros.get("fecha_desde"),
            filtros.get("fecha_hasta"),
        )
        actor_filter = self._resolve_actor_filter(permission_ctx)

        rows = await self._repo.get_acciones_por_dia(
            fecha_desde=fd,
            fecha_hasta=fh,
            materia_id=filtros.get("materia_id"),
            actor_filter=actor_filter,
        )

        items = [AccionesPorDiaItem(fecha=fecha, total=total) for fecha, total in rows]
        return AccionesPorDiaResponse(
            items=items,
            rango=RangoFechasResponse(desde=fd, hasta=fh),
        )

    # ------------------------------------------------------------------
    # 4.6 get_comunicaciones_por_docente
    # ------------------------------------------------------------------

    async def get_comunicaciones_por_docente(
        self,
        filtros: dict,
        permission_ctx: PermissionContext,
    ) -> ComunicacionesPorDocenteResponse:
        """Retorna el agregado de comunicaciones por docente y estado."""
        fd, fh = self._resolve_rango(
            filtros.get("fecha_desde"),
            filtros.get("fecha_hasta"),
        )
        actor_filter = self._resolve_actor_filter(permission_ctx)

        rows = await self._repo.get_comunicaciones_por_docente(
            fecha_desde=fd,
            fecha_hasta=fh,
            materia_id=filtros.get("materia_id"),
            actor_filter=actor_filter,
        )

        # Agrupa filas por actor_id y acumula conteos por estado
        agrupado: dict[UUID, dict] = {}
        for row in rows:
            actor_id = row["actor_id"]
            if actor_id not in agrupado:
                agrupado[actor_id] = {
                    "usuario_id": actor_id,
                    "usuario_nombre": row["usuario_nombre"],
                    "conteos": {
                        "Pendiente": 0,
                        "Enviando": 0,
                        "Enviado": 0,
                        "Error": 0,
                        "Cancelado": 0,
                    },
                }
            estado = row["estado"]
            if estado in agrupado[actor_id]["conteos"]:
                agrupado[actor_id]["conteos"][estado] += row["conteo"]

        items = [
            ComunicacionesPorDocenteItem(
                usuario_id=data["usuario_id"],
                usuario_nombre=data["usuario_nombre"],
                conteos=ConteoEstadosComunicacion(**data["conteos"]),
            )
            for data in agrupado.values()
        ]
        return ComunicacionesPorDocenteResponse(items=items)

    # ------------------------------------------------------------------
    # 4.7 get_interacciones_por_docente_materia
    # ------------------------------------------------------------------

    async def get_interacciones_por_docente_materia(
        self,
        filtros: dict,
        permission_ctx: PermissionContext,
    ) -> InteraccionesPorDocenteMateriaResponse:
        """Retorna interacciones agrupadas por (docente, materia, accion)."""
        fd, fh = self._resolve_rango(
            filtros.get("fecha_desde"),
            filtros.get("fecha_hasta"),
        )
        actor_filter = self._resolve_actor_filter(permission_ctx)

        rows = await self._repo.get_interacciones_por_docente_materia(
            fecha_desde=fd,
            fecha_hasta=fh,
            materia_id=filtros.get("materia_id"),
            usuario_id=filtros.get("usuario_id"),
            actor_filter=actor_filter,
        )

        items = [
            InteraccionesPorDocenteMateriaItem(
                actor_id=row["actor_id"],
                actor_nombre=row["actor_nombre"],
                materia_id=row["materia_id"],
                materia_nombre=row["materia_nombre"],
                accion=row["accion"],
                categoria=self.categoria_for(row["accion"]),
                total=row["total"],
            )
            for row in rows
        ]
        return InteraccionesPorDocenteMateriaResponse(items=items)

    # ------------------------------------------------------------------
    # 4.8 get_ultimas_acciones
    # ------------------------------------------------------------------

    async def get_ultimas_acciones(
        self,
        filtros: dict,
        permission_ctx: PermissionContext,
    ) -> UltimasAccionesResponse:
        """Retorna las últimas N acciones con limit configurable (default 200, max 1000)."""
        limit = filtros.get("limit", self._DEFAULT_LIMIT)
        actor_filter = self._resolve_actor_filter(permission_ctx)

        entries = await self._repo.get_ultimas_acciones(
            limit=limit,
            materia_id=filtros.get("materia_id"),
            usuario_id=filtros.get("usuario_id"),
            accion=filtros.get("accion"),
            actor_filter=actor_filter,
        )

        items = [
            UltimaAccionItem(
                id=entry.id,
                fecha_hora=entry.fecha_hora,
                actor_id=entry.actor_id,
                impersonado_id=entry.impersonado_id,
                materia_id=entry.materia_id,
                accion=entry.accion,
                categoria=self.categoria_for(entry.accion),
                filas_afectadas=entry.filas_afectadas,
                ip=entry.ip,
                user_agent=entry.user_agent,
            )
            for entry in entries
        ]
        return UltimasAccionesResponse(items=items)

    # ------------------------------------------------------------------
    # 4.9 get_catalogo_acciones
    # ------------------------------------------------------------------

    async def get_catalogo_acciones(self) -> CatalogoAccionesResponse:
        """Retorna el catálogo de códigos de acción con su categoría.

        No consulta BD — deriva directamente del enum AuditAction.
        """
        items = [
            CatalogoAccionItem(
                codigo=a.value,
                categoria=self.categoria_for(a.value),
            )
            for a in AuditAction
        ]
        return CatalogoAccionesResponse(items=items)
