"""Service de análisis de atrasados y reportes (C-11).

Motor de análisis: orquesta las queries del repository y aplica
lógica de negocio (scope, empates de ranking, validaciones).

Reglas duras:
- tenant_id y usuario_id SIEMPRE del PermissionContext/CurrentUser (JWT).
- is_propio=True → scope restringido (solo asignaciones del docente).
- is_propio=False → acceso global al tenant.
- Nunca lógica de negocio en Routers.
- Nunca acceso directo a DB en Services (siempre vía Repository).
"""

from datetime import datetime
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analisis_repository import AnalisisRepository
from app.repositories.asignaciones import AsignacionRepository
from app.schemas.analisis import (
    AlumnoAtrasadoSchema,
    AtrasadosResponseSchema,
    EstadoAlumno,
    MonitorItemSchema,
    MonitorResponseSchema,
    MotivoAtrasado,
    NotaFinalItemSchema,
    RankingItemSchema,
    RankingResponseSchema,
    ReporteRapidoSchema,
)
from app.schemas.rbac_schema import PermissionContext


class AnalisisService:
    """Service de análisis de atrasados y reportes.

    Requiere instanciación por request con sesión DB, tenant_id y user_id del JWT.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        tenant_id: UUID,
        usuario_id: UUID,
    ) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.usuario_id = usuario_id
        self._repo = AnalisisRepository(db_session, tenant_id)
        self._asig_repo = AsignacionRepository(db_session, tenant_id)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    async def _verificar_titularidad(self, asignacion_id: UUID) -> None:
        """Verifica que el usuario autenticado es titular de la asignación.

        Lanza 403 si la asignación no le pertenece.
        """
        asig = await self._asig_repo.get_by_id(asignacion_id)
        if asig is None or asig.usuario_id != self.usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a esta asignación",
            )

    def _paginas(self, total: int, page_size: int) -> int:
        if page_size <= 0:
            return 0
        return ceil(total / page_size) if total > 0 else 0

    # ------------------------------------------------------------------
    # 4.1: Atrasados
    # ------------------------------------------------------------------

    async def get_atrasados(
        self,
        asignacion_id: UUID,
        permission_ctx: PermissionContext,
        page: int,
        page_size: int,
    ) -> AtrasadosResponseSchema:
        """Lista paginada de alumnos atrasados de una asignación."""
        if permission_ctx.is_propio:
            await self._verificar_titularidad(asignacion_id)

        items_raw, total = await self._repo.get_atrasados(asignacion_id, page, page_size)

        items = [
            AlumnoAtrasadoSchema(
                entrada_padron_id=row["entrada_padron_id"],
                alumno_nombre=row["alumno_nombre"],
                alumno_email=row["alumno_email"],
                motivo=MotivoAtrasado(row["motivo"]),
                actividades_faltantes_count=row["actividades_faltantes_count"],
                actividades_reprobadas_count=row["actividades_reprobadas_count"],
            )
            for row in items_raw
        ]

        return AtrasadosResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )

    # ------------------------------------------------------------------
    # 4.2: Ranking
    # ------------------------------------------------------------------

    async def get_ranking(
        self,
        asignacion_id: UUID,
        permission_ctx: PermissionContext,
    ) -> RankingResponseSchema:
        """Ranking de actividades aprobadas con manejo de empates (RN-09)."""
        if permission_ctx.is_propio:
            await self._verificar_titularidad(asignacion_id)

        rows = await self._repo.get_ranking(asignacion_id)

        # Construir posiciones con manejo de empates
        # Alumnos con el mismo número de aprobadas → misma posición
        # Desempate secundario: ya viene ordenado por apellido desde el repo
        items: list[RankingItemSchema] = []
        posicion_actual = 1
        ultimo_aprobadas = None

        for i, row in enumerate(rows):
            aprobadas = row["actividades_aprobadas"]
            if aprobadas != ultimo_aprobadas:
                posicion_actual = i + 1
                ultimo_aprobadas = aprobadas

            items.append(
                RankingItemSchema(
                    posicion=posicion_actual,
                    entrada_padron_id=row["entrada_padron_id"],
                    alumno_nombre=row["alumno_nombre"],
                    actividades_aprobadas=aprobadas,
                )
            )

        return RankingResponseSchema(items=items, total=len(items))

    # ------------------------------------------------------------------
    # 4.3: Reporte rápido
    # ------------------------------------------------------------------

    async def get_reporte_rapido(
        self,
        asignacion_id: UUID,
        permission_ctx: PermissionContext,
    ) -> ReporteRapidoSchema:
        """Métricas consolidadas de una asignación."""
        if permission_ctx.is_propio:
            await self._verificar_titularidad(asignacion_id)

        metricas = await self._repo.get_metricas_rapidas(asignacion_id)

        total_alumnos = metricas["total_alumnos"]
        con_aprobadas = metricas["con_aprobadas"]
        pct_aprobacion = (
            round((con_aprobadas / total_alumnos) * 100, 2)
            if total_alumnos > 0
            else 0.0
        )

        return ReporteRapidoSchema(
            total_alumnos=total_alumnos,
            total_actividades=metricas["total_actividades"],
            con_aprobadas=con_aprobadas,
            atrasados=metricas["atrasados"],
            pct_aprobacion=pct_aprobacion,
            sin_datos=metricas["sin_datos"],
        )

    # ------------------------------------------------------------------
    # 4.4: Notas finales
    # ------------------------------------------------------------------

    async def get_notas_finales(
        self,
        asignacion_id: UUID,
        actividad_ids: list[str],
        permission_ctx: PermissionContext,
    ) -> list[NotaFinalItemSchema]:
        """Promedio de nota_numerica sobre actividades seleccionadas por alumno.

        Lanza 422 si la selección no incluye actividades numéricas.
        """
        if permission_ctx.is_propio:
            await self._verificar_titularidad(asignacion_id)

        if not actividad_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Debes seleccionar al menos una actividad numérica.",
            )

        rows = await self._repo.get_notas_finales(asignacion_id, actividad_ids)

        # Verificar que al menos alguna calificación numérica existe para la selección
        tiene_numericas = any(row["nota_final"] is not None for row in rows)
        if not tiene_numericas and rows:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Las actividades seleccionadas no contienen calificaciones numéricas.",
            )

        return [
            NotaFinalItemSchema(
                entrada_padron_id=row["entrada_padron_id"],
                alumno_nombre=row["alumno_nombre"],
                alumno_email=row["alumno_email"],
                nota_final=row["nota_final"],
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # 4.5: TPs sin corregir
    # ------------------------------------------------------------------

    async def get_tps_sin_corregir(
        self,
        asignacion_id: UUID,
        permission_ctx: PermissionContext,
    ) -> list[dict]:
        """TPs textuales sin nota registrada (RN-07/08)."""
        if permission_ctx.is_propio:
            await self._verificar_titularidad(asignacion_id)

        return await self._repo.get_tps_sin_corregir(asignacion_id)

    # ------------------------------------------------------------------
    # 4.6: Monitor general (COORDINADOR/ADMIN únicamente)
    # ------------------------------------------------------------------

    async def get_monitor_general(
        self,
        filtros: dict,
        permission_ctx: PermissionContext,
        page: int,
        page_size: int,
    ) -> MonitorResponseSchema:
        """Vista transversal de todos los alumnos del tenant.

        Solo COORDINADOR y ADMIN (is_propio=False). Lanza 403 si is_propio.
        """
        if permission_ctx.is_propio:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El monitor general requiere acceso global (COORDINADOR o ADMIN)",
            )

        items_raw, total = await self._repo.get_monitor_general(filtros, page, page_size)
        return self._build_monitor_response(items_raw, total, page, page_size)

    # ------------------------------------------------------------------
    # 4.7: Monitor propio (TUTOR/PROFESOR)
    # ------------------------------------------------------------------

    async def get_monitor_propio(
        self,
        filtros: dict,
        permission_ctx: PermissionContext,
        page: int,
        page_size: int,
    ) -> MonitorResponseSchema:
        """Vista filtrada a las asignaciones del usuario autenticado."""
        items_raw, total = await self._repo.get_monitor_propio(
            usuario_id=self.usuario_id,
            filtros=filtros,
            page=page,
            page_size=page_size,
        )
        return self._build_monitor_response(items_raw, total, page, page_size)

    # ------------------------------------------------------------------
    # 4.8: Monitor global (COORDINADOR/ADMIN + rango fechas)
    # ------------------------------------------------------------------

    async def get_monitor_global(
        self,
        filtros: dict,
        fecha_desde: datetime | None,
        fecha_hasta: datetime | None,
        permission_ctx: PermissionContext,
        page: int,
        page_size: int,
    ) -> MonitorResponseSchema:
        """Monitor general extendido con rango de fechas.

        Solo COORDINADOR y ADMIN. Lanza 403 si is_propio.
        """
        if permission_ctx.is_propio:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El monitor global requiere acceso global (COORDINADOR o ADMIN)",
            )

        items_raw, total = await self._repo.get_monitor_global(
            filtros=filtros,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            page=page,
            page_size=page_size,
        )
        return self._build_monitor_response(items_raw, total, page, page_size)

    # ------------------------------------------------------------------
    # Helper: construir MonitorResponseSchema
    # ------------------------------------------------------------------

    def _build_monitor_response(
        self,
        items_raw: list[dict],
        total: int,
        page: int,
        page_size: int,
    ) -> MonitorResponseSchema:
        items = [
            MonitorItemSchema(
                entrada_padron_id=row["entrada_padron_id"],
                alumno_nombre=row["alumno_nombre"],
                email=row["email"],
                materia_id=row["materia_id"],
                materia_nombre=row["materia_nombre"],
                actividades_aprobadas=row["actividades_aprobadas"],
                actividades_totales=row["actividades_totales"],
                estado=EstadoAlumno(row["estado"]),
            )
            for row in items_raw
        ]

        return MonitorResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )
