"""Repositorio de análisis de atrasados y reportes (C-11).

Todas las queries filtran por tenant_id (row-level isolation).
Lógica de negocio pertenece al Service, aquí solo queries de agregación.

Nota sobre asignacion_id:
  Una asignacion vincula usuario_importador_id con materia_id.
  Las calificaciones se filtran por (tenant_id, usuario_importador_id, materia_id).
  Para las queries de análisis necesitamos JOIN con Asignacion para obtener
  materia_id y usuario_importador_id.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.calificacion import Calificacion
from app.models.estructura import Materia
from app.models.padron import EntradaPadron, VersionPadron


class AnalisisRepository:
    """Repository de análisis: queries de agregación sobre calificaciones y padrón."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        self.db_session = db_session
        self.tenant_id = tenant_id

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    async def _get_asignacion(self, asignacion_id: UUID) -> Asignacion | None:
        """Obtiene una asignación del tenant por ID."""
        query = select(Asignacion).where(
            Asignacion.id == asignacion_id,
            Asignacion.tenant_id == self.tenant_id,
            Asignacion.deleted_at.is_(None),
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # 3.1: Entradas con calificaciones
    # ------------------------------------------------------------------

    async def get_entradas_con_calificaciones(
        self,
        asignacion_id: UUID,
    ) -> list[dict]:
        """Retorna EntradaPadron activas + sus Calificacion (JOIN).

        Cada fila: entrada_padron_id, nombre, apellidos, email,
                   calificacion (puede ser None si no tiene).
        """
        asig = await self._get_asignacion(asignacion_id)
        if asig is None:
            return []

        # EntradaPadron activas en versiones del padrón de la materia del docente
        # (filtra por materia_id de la asignación)
        query = (
            select(
                EntradaPadron.id.label("entrada_padron_id"),
                EntradaPadron.nombre,
                EntradaPadron.apellidos,
                EntradaPadron.email,
                Calificacion.actividad,
                Calificacion.nota_numerica,
                Calificacion.nota_textual,
                Calificacion.aprobado,
            )
            .select_from(EntradaPadron)
            .join(
                VersionPadron,
                and_(
                    VersionPadron.id == EntradaPadron.version_id,
                    VersionPadron.materia_id == asig.materia_id,
                    VersionPadron.tenant_id == self.tenant_id,
                    VersionPadron.activa.is_(True),
                    VersionPadron.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                Calificacion,
                and_(
                    Calificacion.entrada_padron_id == EntradaPadron.id,
                    Calificacion.usuario_importador_id == asig.usuario_id,
                    Calificacion.materia_id == asig.materia_id,
                    Calificacion.tenant_id == self.tenant_id,
                    Calificacion.deleted_at.is_(None),
                ),
            )
            .where(
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
        )
        result = await self.db_session.execute(query)
        return [row._asdict() for row in result.all()]

    # ------------------------------------------------------------------
    # 3.2: Atrasados paginados
    # ------------------------------------------------------------------

    async def get_atrasados(
        self,
        asignacion_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        """Query paginada de alumnos atrasados.

        Atrasado = sin calificaciones (sin_datos) O tiene aprobado=False en alguna.
        Retorna (items, total).
        """
        asig = await self._get_asignacion(asignacion_id)
        if asig is None:
            return [], 0

        # Subquery: contar aprobadas y reprobadas por alumno
        cal_subq = (
            select(
                Calificacion.entrada_padron_id,
                func.count(Calificacion.id).label("total_cal"),
                func.sum(
                    case((Calificacion.aprobado.is_(True), 1), else_=0)
                ).label("aprobadas"),
                func.sum(
                    case((Calificacion.aprobado.is_(False), 1), else_=0)
                ).label("reprobadas"),
            )
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.usuario_importador_id == asig.usuario_id,
                Calificacion.materia_id == asig.materia_id,
                Calificacion.deleted_at.is_(None),
            )
            .group_by(Calificacion.entrada_padron_id)
            .subquery()
        )

        # Query principal: EntradaPadron con LEFT JOIN a calificaciones
        base = (
            select(
                EntradaPadron.id.label("entrada_padron_id"),
                (EntradaPadron.nombre + " " + EntradaPadron.apellidos).label("alumno_nombre"),
                EntradaPadron.email.label("alumno_email"),
                cal_subq.c.total_cal,
                cal_subq.c.aprobadas,
                cal_subq.c.reprobadas,
            )
            .select_from(EntradaPadron)
            .join(
                VersionPadron,
                and_(
                    VersionPadron.id == EntradaPadron.version_id,
                    VersionPadron.materia_id == asig.materia_id,
                    VersionPadron.tenant_id == self.tenant_id,
                    VersionPadron.activa.is_(True),
                    VersionPadron.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                cal_subq,
                cal_subq.c.entrada_padron_id == EntradaPadron.id,
            )
            .where(
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.deleted_at.is_(None),
                # Atrasado: sin calificaciones O tiene alguna reprobada
                or_(
                    cal_subq.c.total_cal.is_(None),
                    cal_subq.c.reprobadas > 0,
                ),
            )
        )

        # Count total
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.db_session.execute(count_q)).scalar_one()

        # Paginated
        offset = (page - 1) * page_size
        items_q = base.order_by(EntradaPadron.apellidos, EntradaPadron.nombre).limit(page_size).offset(offset)
        rows = (await self.db_session.execute(items_q)).all()

        items = []
        for row in rows:
            total_cal = row.total_cal
            aprobadas = row.aprobadas or 0
            reprobadas = row.reprobadas or 0

            if total_cal is None:
                motivo = "sin_datos"
                faltantes = 0
                reprobadas_count = 0
            elif reprobadas > 0:
                motivo = "nota_insuficiente"
                faltantes = 0
                reprobadas_count = int(reprobadas)
            else:
                motivo = "actividades_faltantes"
                faltantes = 0
                reprobadas_count = 0

            items.append({
                "entrada_padron_id": row.entrada_padron_id,
                "alumno_nombre": row.alumno_nombre,
                "alumno_email": row.alumno_email,
                "motivo": motivo,
                "actividades_faltantes_count": faltantes,
                "actividades_reprobadas_count": reprobadas_count,
            })

        return items, total

    # ------------------------------------------------------------------
    # 3.3: Ranking
    # ------------------------------------------------------------------

    async def get_ranking(
        self,
        asignacion_id: UUID,
    ) -> list[dict]:
        """COUNT de aprobado=True por alumno; solo alumnos con al menos 1 (RN-09).

        Orden: descendente por actividades_aprobadas, luego ascendente por apellido.
        """
        asig = await self._get_asignacion(asignacion_id)
        if asig is None:
            return []

        query = (
            select(
                Calificacion.entrada_padron_id,
                func.count(Calificacion.id).label("actividades_aprobadas"),
                func.min(EntradaPadron.apellidos).label("apellidos"),
                func.min(
                    EntradaPadron.nombre + " " + EntradaPadron.apellidos
                ).label("alumno_nombre"),
            )
            .select_from(Calificacion)
            .join(
                EntradaPadron,
                EntradaPadron.id == Calificacion.entrada_padron_id,
            )
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.usuario_importador_id == asig.usuario_id,
                Calificacion.materia_id == asig.materia_id,
                Calificacion.deleted_at.is_(None),
                Calificacion.aprobado.is_(True),
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
            .group_by(Calificacion.entrada_padron_id)
            .having(func.count(Calificacion.id) > 0)
            .order_by(
                func.count(Calificacion.id).desc(),
                func.min(EntradaPadron.apellidos).asc(),
            )
        )

        result = await self.db_session.execute(query)
        return [
            {
                "entrada_padron_id": row.entrada_padron_id,
                "alumno_nombre": row.alumno_nombre,
                "actividades_aprobadas": row.actividades_aprobadas,
                "apellidos": row.apellidos,
            }
            for row in result.all()
        ]

    # ------------------------------------------------------------------
    # 3.4: Métricas rápidas
    # ------------------------------------------------------------------

    async def get_metricas_rapidas(
        self,
        asignacion_id: UUID,
    ) -> dict:
        """Un solo query con agregaciones COUNT para métricas del reporte rápido.

        Retorna: total_alumnos, total_actividades, con_aprobadas, atrasados, sin_datos.
        """
        asig = await self._get_asignacion(asignacion_id)
        if asig is None:
            return {
                "total_alumnos": 0,
                "total_actividades": 0,
                "con_aprobadas": 0,
                "atrasados": 0,
                "sin_datos": True,
            }

        # Total de alumnos en el padrón activo de esta materia
        padron_q = (
            select(func.count(EntradaPadron.id))
            .select_from(EntradaPadron)
            .join(
                VersionPadron,
                and_(
                    VersionPadron.id == EntradaPadron.version_id,
                    VersionPadron.materia_id == asig.materia_id,
                    VersionPadron.tenant_id == self.tenant_id,
                    VersionPadron.activa.is_(True),
                    VersionPadron.deleted_at.is_(None),
                ),
            )
            .where(
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
        )
        total_alumnos = (await self.db_session.execute(padron_q)).scalar_one()

        # Total de calificaciones (actividades) y alumnos con al menos 1 aprobada
        cal_agg_q = select(
            func.count(Calificacion.id).label("total_actividades"),
            func.count(func.distinct(Calificacion.entrada_padron_id)).label("con_alguna_cal"),
        ).where(
            Calificacion.tenant_id == self.tenant_id,
            Calificacion.usuario_importador_id == asig.usuario_id,
            Calificacion.materia_id == asig.materia_id,
            Calificacion.deleted_at.is_(None),
        )
        cal_row = (await self.db_session.execute(cal_agg_q)).one()
        total_actividades = cal_row.total_actividades or 0

        if total_actividades == 0:
            return {
                "total_alumnos": total_alumnos,
                "total_actividades": 0,
                "con_aprobadas": 0,
                "atrasados": total_alumnos,
                "sin_datos": True,
            }

        # Alumnos con al menos una aprobada
        con_aprobadas_q = (
            select(func.count(func.distinct(Calificacion.entrada_padron_id)))
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.usuario_importador_id == asig.usuario_id,
                Calificacion.materia_id == asig.materia_id,
                Calificacion.deleted_at.is_(None),
                Calificacion.aprobado.is_(True),
            )
        )
        con_aprobadas = (await self.db_session.execute(con_aprobadas_q)).scalar_one() or 0

        # Atrasados = alumnos con alguna reprobada o sin calificaciones
        reprobados_q = (
            select(func.count(func.distinct(Calificacion.entrada_padron_id)))
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.usuario_importador_id == asig.usuario_id,
                Calificacion.materia_id == asig.materia_id,
                Calificacion.deleted_at.is_(None),
                Calificacion.aprobado.is_(False),
            )
        )
        con_reprobadas = (await self.db_session.execute(reprobados_q)).scalar_one() or 0
        alumnos_con_cal = cal_row.con_alguna_cal or 0
        sin_calificaciones = max(0, total_alumnos - alumnos_con_cal)
        atrasados = con_reprobadas + sin_calificaciones

        return {
            "total_alumnos": total_alumnos,
            "total_actividades": total_actividades,
            "con_aprobadas": con_aprobadas,
            "atrasados": atrasados,
            "sin_datos": False,
        }

    # ------------------------------------------------------------------
    # 3.5: Notas finales
    # ------------------------------------------------------------------

    async def get_notas_finales(
        self,
        asignacion_id: UUID,
        actividad_ids: list[str],
    ) -> list[dict]:
        """AVG de nota_numerica sobre actividades seleccionadas por alumno.

        Actividades sin nota cuentan como 0.0 en el promedio.
        actividad_ids son los nombres de las actividades (campo str en Calificacion).
        """
        asig = await self._get_asignacion(asignacion_id)
        if asig is None:
            return []

        # Alumnos del padrón activo
        padron_q = (
            select(
                EntradaPadron.id.label("entrada_padron_id"),
                (EntradaPadron.nombre + " " + EntradaPadron.apellidos).label("alumno_nombre"),
                EntradaPadron.email.label("alumno_email"),
            )
            .select_from(EntradaPadron)
            .join(
                VersionPadron,
                and_(
                    VersionPadron.id == EntradaPadron.version_id,
                    VersionPadron.materia_id == asig.materia_id,
                    VersionPadron.tenant_id == self.tenant_id,
                    VersionPadron.activa.is_(True),
                    VersionPadron.deleted_at.is_(None),
                ),
            )
            .where(
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
        )
        padron_result = await self.db_session.execute(padron_q)
        alumnos = padron_result.all()

        if not alumnos:
            return []

        # Calificaciones numéricas de las actividades seleccionadas
        cal_q = (
            select(
                Calificacion.entrada_padron_id,
                Calificacion.actividad,
                Calificacion.nota_numerica,
            )
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.usuario_importador_id == asig.usuario_id,
                Calificacion.materia_id == asig.materia_id,
                Calificacion.deleted_at.is_(None),
                Calificacion.actividad.in_(actividad_ids),
                Calificacion.nota_numerica.is_not(None),
            )
        )
        cal_result = await self.db_session.execute(cal_q)
        cal_rows = cal_result.all()

        # Índice: entrada_padron_id → {actividad → nota}
        notas_index: dict[UUID, dict[str, float]] = {}
        for row in cal_rows:
            if row.entrada_padron_id not in notas_index:
                notas_index[row.entrada_padron_id] = {}
            notas_index[row.entrada_padron_id][row.actividad] = row.nota_numerica or 0.0

        num_actividades = len(actividad_ids)
        resultados = []
        for alumno in alumnos:
            notas_alumno = notas_index.get(alumno.entrada_padron_id, {})
            # Actividades sin nota cuentan como 0.0
            suma = sum(notas_alumno.get(act, 0.0) for act in actividad_ids)
            nota_final = round(suma / num_actividades, 2) if num_actividades > 0 else None
            resultados.append({
                "entrada_padron_id": alumno.entrada_padron_id,
                "alumno_nombre": alumno.alumno_nombre,
                "alumno_email": alumno.alumno_email,
                "nota_final": nota_final,
            })

        return resultados

    # ------------------------------------------------------------------
    # 3.6: TPs sin corregir
    # ------------------------------------------------------------------

    async def get_tps_sin_corregir(
        self,
        asignacion_id: UUID,
    ) -> list[dict]:
        """TPs textuales finalizados sin nota_textual registrada (RN-07/08).

        Retorna lista de calificaciones con nota_textual IS NULL
        (entregas textuales pendientes de corrección).
        """
        asig = await self._get_asignacion(asignacion_id)
        if asig is None:
            return []

        # Calificaciones de escala textual sin nota registrada
        # En el modelo actual: nota_textual IS NULL pero tiene registro = TP sin corregir
        # (el registro se creó al importar el reporte de finalización)
        query = (
            select(
                EntradaPadron.id.label("entrada_padron_id"),
                (EntradaPadron.nombre + " " + EntradaPadron.apellidos).label("alumno_nombre"),
                EntradaPadron.email.label("alumno_email"),
                Calificacion.actividad,
                Calificacion.importado_at.label("fecha_finalizacion"),
            )
            .select_from(Calificacion)
            .join(
                EntradaPadron,
                EntradaPadron.id == Calificacion.entrada_padron_id,
            )
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.usuario_importador_id == asig.usuario_id,
                Calificacion.materia_id == asig.materia_id,
                Calificacion.deleted_at.is_(None),
                Calificacion.nota_textual.is_(None),
                Calificacion.nota_numerica.is_(None),
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
            .order_by(EntradaPadron.apellidos, Calificacion.actividad)
        )

        result = await self.db_session.execute(query)
        return [
            {
                "entrada_padron_id": row.entrada_padron_id,
                "alumno_nombre": row.alumno_nombre,
                "alumno_email": row.alumno_email,
                "actividad": row.actividad,
                "fecha_finalizacion": row.fecha_finalizacion,
            }
            for row in result.all()
        ]

    # ------------------------------------------------------------------
    # 3.7: Monitor general (multi-asignación)
    # ------------------------------------------------------------------

    async def get_monitor_general(
        self,
        filtros: dict,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        """Vista paginada multi-asignación de todos los alumnos del tenant.

        Filtros dinámicos: materia_id, regional, comision, alumno, estado.
        """
        return await self._monitor_query(
            filtros=filtros,
            usuario_id=None,
            fecha_desde=None,
            fecha_hasta=None,
            page=page,
            page_size=page_size,
        )

    # ------------------------------------------------------------------
    # 3.8: Monitor propio (filtrado por usuario)
    # ------------------------------------------------------------------

    async def get_monitor_propio(
        self,
        usuario_id: UUID,
        filtros: dict,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        """Vista paginada de alumnos de las asignaciones del docente autenticado."""
        return await self._monitor_query(
            filtros=filtros,
            usuario_id=usuario_id,
            fecha_desde=None,
            fecha_hasta=None,
            page=page,
            page_size=page_size,
        )

    # ------------------------------------------------------------------
    # 3.9: Monitor global (con rango de fechas)
    # ------------------------------------------------------------------

    async def get_monitor_global(
        self,
        filtros: dict,
        fecha_desde: datetime | None,
        fecha_hasta: datetime | None,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        """Extiende el monitor general con filtro de rango de fechas."""
        return await self._monitor_query(
            filtros=filtros,
            usuario_id=None,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            page=page,
            page_size=page_size,
        )

    # ------------------------------------------------------------------
    # Query compartida del monitor
    # ------------------------------------------------------------------

    async def _monitor_query(
        self,
        filtros: dict,
        usuario_id: UUID | None,
        fecha_desde: datetime | None,
        fecha_hasta: datetime | None,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        """Query unificada para los tres tipos de monitor.

        Agrega calificaciones por (alumno, materia) y calcula estado.
        """
        # Subquery: conteos de calificaciones por (entrada_padron_id, materia_id)
        cal_conditions = [
            Calificacion.tenant_id == self.tenant_id,
            Calificacion.deleted_at.is_(None),
        ]

        if usuario_id is not None:
            # Monitor propio: filtrar por asignaciones del usuario
            cal_conditions.append(Calificacion.usuario_importador_id == usuario_id)

        if fecha_desde is not None:
            cal_conditions.append(Calificacion.created_at >= fecha_desde)
        if fecha_hasta is not None:
            cal_conditions.append(Calificacion.created_at <= fecha_hasta)

        cal_subq = (
            select(
                Calificacion.entrada_padron_id,
                Calificacion.materia_id,
                func.count(Calificacion.id).label("actividades_totales"),
                func.sum(
                    case((Calificacion.aprobado.is_(True), 1), else_=0)
                ).label("actividades_aprobadas"),
            )
            .where(*cal_conditions)
            .group_by(Calificacion.entrada_padron_id, Calificacion.materia_id)
            .subquery()
        )

        # Filtro de estado (calculado)
        estado_expr = case(
            (cal_subq.c.actividades_totales.is_(None), "sin_datos"),
            (cal_subq.c.actividades_aprobadas < cal_subq.c.actividades_totales, "atrasado"),
            else_="al_dia",
        )

        base = (
            select(
                EntradaPadron.id.label("entrada_padron_id"),
                (EntradaPadron.nombre + " " + EntradaPadron.apellidos).label("alumno_nombre"),
                EntradaPadron.email.label("email"),
                Materia.id.label("materia_id"),
                Materia.nombre.label("materia_nombre"),
                func.coalesce(cal_subq.c.actividades_aprobadas, 0).label("actividades_aprobadas"),
                func.coalesce(cal_subq.c.actividades_totales, 0).label("actividades_totales"),
                estado_expr.label("estado"),
                EntradaPadron.regional,
                EntradaPadron.comision,
            )
            .select_from(EntradaPadron)
            .join(
                VersionPadron,
                and_(
                    VersionPadron.id == EntradaPadron.version_id,
                    VersionPadron.tenant_id == self.tenant_id,
                    VersionPadron.activa.is_(True),
                    VersionPadron.deleted_at.is_(None),
                ),
            )
            .join(
                Materia,
                and_(
                    Materia.id == VersionPadron.materia_id,
                    Materia.tenant_id == self.tenant_id,
                    Materia.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                cal_subq,
                and_(
                    cal_subq.c.entrada_padron_id == EntradaPadron.id,
                    cal_subq.c.materia_id == VersionPadron.materia_id,
                ),
            )
            .where(
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
        )

        # Filtros dinámicos
        if filtros.get("materia_id"):
            base = base.where(Materia.id == filtros["materia_id"])
        if filtros.get("regional"):
            base = base.where(
                EntradaPadron.regional.ilike(f"%{filtros['regional']}%")
            )
        if filtros.get("comision"):
            base = base.where(
                EntradaPadron.comision.ilike(f"%{filtros['comision']}%")
            )
        if filtros.get("alumno"):
            search = f"%{filtros['alumno']}%"
            base = base.where(
                or_(
                    EntradaPadron.nombre.ilike(search),
                    EntradaPadron.apellidos.ilike(search),
                )
            )
        if filtros.get("estado_actividad"):
            estado_val = filtros["estado_actividad"]
            if estado_val == "sin_datos":
                base = base.where(cal_subq.c.actividades_totales.is_(None))
            elif estado_val == "atrasado":
                base = base.where(
                    and_(
                        cal_subq.c.actividades_totales.is_not(None),
                        cal_subq.c.actividades_aprobadas < cal_subq.c.actividades_totales,
                    )
                )
            elif estado_val == "al_dia":
                base = base.where(
                    and_(
                        cal_subq.c.actividades_totales.is_not(None),
                        cal_subq.c.actividades_aprobadas >= cal_subq.c.actividades_totales,
                    )
                )

        # Count total
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.db_session.execute(count_q)).scalar_one()

        # Paginated
        offset = (page - 1) * page_size
        items_q = base.order_by(EntradaPadron.apellidos, Materia.nombre).limit(page_size).offset(offset)
        rows = (await self.db_session.execute(items_q)).all()

        items = [
            {
                "entrada_padron_id": row.entrada_padron_id,
                "alumno_nombre": row.alumno_nombre,
                "email": row.email,
                "materia_id": row.materia_id,
                "materia_nombre": row.materia_nombre,
                "actividades_aprobadas": row.actividades_aprobadas or 0,
                "actividades_totales": row.actividades_totales or 0,
                "estado": row.estado,
            }
            for row in rows
        ]

        return items, total
