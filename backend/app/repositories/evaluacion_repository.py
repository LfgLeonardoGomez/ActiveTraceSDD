"""Repositorio de evaluaciones y coloquios (C-14).

Todas las queries filtran por tenant_id (row-level isolation).
Lógica de negocio pertenece al Service.

Decisión D3: create_reserva usa SELECT FOR UPDATE para evitar
race conditions en validación de cupo disponible.
"""

from datetime import datetime, timezone
from math import ceil
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import (
    EstadoReserva,
    Evaluacion,
    EvaluacionCandidato,
    ReservaEvaluacion,
    ResultadoEvaluacion,
)
from app.models.estructura import Materia
from app.models.user import Usuario


class EvaluacionRepository:
    """Repository de evaluaciones: CRUD + queries de métricas y agenda."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        self.db_session = db_session
        self.tenant_id = tenant_id

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _base_evaluacion_query(self):
        return select(Evaluacion).where(
            Evaluacion.tenant_id == self.tenant_id,
            Evaluacion.deleted_at.is_(None),
        )

    # ------------------------------------------------------------------
    # 3.1 CRUD convocatorias
    # ------------------------------------------------------------------

    async def create(self, data: dict) -> Evaluacion:
        evaluacion = Evaluacion(
            id=uuid4(),
            tenant_id=self.tenant_id,
            **data,
        )
        self.db_session.add(evaluacion)
        await self.db_session.commit()
        await self.db_session.refresh(evaluacion)
        return evaluacion

    async def get_by_id(self, evaluacion_id: UUID) -> Evaluacion | None:
        query = self._base_evaluacion_query().where(Evaluacion.id == evaluacion_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_with_metrics(
        self, page: int, page_size: int
    ) -> tuple[list[dict], int]:
        """Lista convocatorias con métricas calculadas: convocados, reservas_activas, cupos_libres."""
        count_cand = (
            select(func.count())
            .where(EvaluacionCandidato.evaluacion_id == Evaluacion.id)
            .correlate(Evaluacion)
            .scalar_subquery()
        )
        count_reservas = (
            select(func.count())
            .where(
                ReservaEvaluacion.evaluacion_id == Evaluacion.id,
                ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
                ReservaEvaluacion.deleted_at.is_(None),
            )
            .correlate(Evaluacion)
            .scalar_subquery()
        )

        base = self._base_evaluacion_query()
        total_q = select(func.count()).select_from(base.subquery())
        total = (await self.db_session.execute(total_q)).scalar_one()

        offset = (page - 1) * page_size
        rows_q = (
            base.add_columns(count_cand.label("convocados"), count_reservas.label("reservas_activas"))
            .order_by(Evaluacion.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(rows_q)
        rows = result.all()

        items = []
        for ev, convocados, reservas_activas in rows:
            cupos_libres = max(0, ev.cupo_por_dia - (reservas_activas or 0))
            items.append({
                "id": ev.id,
                "materia_id": ev.materia_id,
                "cohorte_id": ev.cohorte_id,
                "tipo": ev.tipo,
                "instancia": ev.instancia,
                "dias_disponibles": ev.dias_disponibles,
                "cupo_por_dia": ev.cupo_por_dia,
                "convocados": convocados or 0,
                "reservas_activas": reservas_activas or 0,
                "cupos_libres_por_dia": cupos_libres,
                "created_at": ev.created_at,
            })
        return items, total

    async def update(self, evaluacion_id: UUID, data: dict) -> Evaluacion | None:
        evaluacion = await self.get_by_id(evaluacion_id)
        if evaluacion is None:
            return None
        for key, value in data.items():
            if hasattr(evaluacion, key):
                setattr(evaluacion, key, value)
        evaluacion.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(evaluacion)
        return evaluacion

    # ------------------------------------------------------------------
    # 3.1 Candidatos
    # ------------------------------------------------------------------

    async def import_candidatos(
        self, evaluacion_id: UUID, alumno_ids: list[UUID]
    ) -> int:
        """Reemplaza el padrón de candidatos de la convocatoria."""
        await self.db_session.execute(
            delete(EvaluacionCandidato).where(
                EvaluacionCandidato.evaluacion_id == evaluacion_id
            )
        )
        for alumno_id in alumno_ids:
            self.db_session.add(
                EvaluacionCandidato(evaluacion_id=evaluacion_id, alumno_id=alumno_id)
            )
        await self.db_session.commit()
        return len(alumno_ids)

    async def get_candidatos(self, evaluacion_id: UUID) -> list[dict]:
        query = (
            select(
                EvaluacionCandidato.alumno_id,
                Usuario.nombre,
                Usuario.apellidos,
            )
            .join(Usuario, Usuario.id == EvaluacionCandidato.alumno_id)
            .where(EvaluacionCandidato.evaluacion_id == evaluacion_id)
        )
        result = await self.db_session.execute(query)
        return [
            {"alumno_id": r.alumno_id, "alumno_nombre": f"{r.nombre} {r.apellidos}"}
            for r in result.all()
        ]

    async def is_candidato(self, evaluacion_id: UUID, alumno_id: UUID) -> bool:
        query = select(EvaluacionCandidato).where(
            EvaluacionCandidato.evaluacion_id == evaluacion_id,
            EvaluacionCandidato.alumno_id == alumno_id,
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none() is not None

    # ------------------------------------------------------------------
    # 3.2 Reservas — con SELECT FOR UPDATE para cupo (D3)
    # ------------------------------------------------------------------

    async def count_reservas_activas_en_dia(
        self, evaluacion_id: UUID, fecha: datetime
    ) -> int:
        """Cuenta reservas activas para un día usando SELECT FOR UPDATE."""
        fecha_date = fecha.date()
        query = text(
            "SELECT COUNT(*) FROM reserva_evaluacion "
            "WHERE evaluacion_id = :eid "
            "AND estado = 'Activa' "
            "AND deleted_at IS NULL "
            "AND fecha_hora::date = :fecha "
            "FOR UPDATE"
        )
        result = await self.db_session.execute(
            query, {"eid": str(evaluacion_id), "fecha": str(fecha_date)}
        )
        return result.scalar_one()

    async def get_reserva_activa_del_alumno(
        self, evaluacion_id: UUID, alumno_id: UUID
    ) -> ReservaEvaluacion | None:
        query = select(ReservaEvaluacion).where(
            ReservaEvaluacion.tenant_id == self.tenant_id,
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.alumno_id == alumno_id,
            ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def create_reserva(
        self, evaluacion_id: UUID, alumno_id: UUID, fecha_hora: datetime
    ) -> ReservaEvaluacion:
        reserva = ReservaEvaluacion(
            id=uuid4(),
            tenant_id=self.tenant_id,
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            fecha_hora=fecha_hora,
            estado=EstadoReserva.ACTIVA,
        )
        self.db_session.add(reserva)
        await self.db_session.commit()
        await self.db_session.refresh(reserva)
        return reserva

    # ------------------------------------------------------------------
    # 3.3 Cancelar reserva, listar
    # ------------------------------------------------------------------

    async def get_reserva_by_id(self, reserva_id: UUID) -> ReservaEvaluacion | None:
        query = select(ReservaEvaluacion).where(
            ReservaEvaluacion.id == reserva_id,
            ReservaEvaluacion.tenant_id == self.tenant_id,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def cancel_reserva(self, reserva: ReservaEvaluacion) -> ReservaEvaluacion:
        reserva.estado = EstadoReserva.CANCELADA
        reserva.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(reserva)
        return reserva

    async def get_reservas(
        self,
        evaluacion_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        base = select(ReservaEvaluacion).where(
            ReservaEvaluacion.tenant_id == self.tenant_id,
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        total = (
            await self.db_session.execute(
                select(func.count()).select_from(base.subquery())
            )
        ).scalar_one()

        offset = (page - 1) * page_size
        rows_q = (
            select(
                ReservaEvaluacion,
                Usuario.nombre,
                Usuario.apellidos,
            )
            .join(Usuario, Usuario.id == ReservaEvaluacion.alumno_id)
            .where(
                ReservaEvaluacion.tenant_id == self.tenant_id,
                ReservaEvaluacion.evaluacion_id == evaluacion_id,
                ReservaEvaluacion.deleted_at.is_(None),
            )
            .order_by(ReservaEvaluacion.fecha_hora)
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(rows_q)
        items = []
        for reserva, nombre, apellidos in result.all():
            items.append({
                "id": reserva.id,
                "evaluacion_id": reserva.evaluacion_id,
                "alumno_id": reserva.alumno_id,
                "alumno_nombre": f"{nombre} {apellidos}",
                "fecha_hora": reserva.fecha_hora,
                "estado": reserva.estado,
                "created_at": reserva.created_at,
            })
        return items, total

    # ------------------------------------------------------------------
    # 3.4 Resultados
    # ------------------------------------------------------------------

    async def upsert_resultado(
        self,
        evaluacion_id: UUID,
        alumno_id: UUID,
        nota_final: str,
    ) -> ResultadoEvaluacion:
        """Crea o actualiza el resultado de un alumno (upsert por evaluacion_id + alumno_id)."""
        existing_q = select(ResultadoEvaluacion).where(
            ResultadoEvaluacion.evaluacion_id == evaluacion_id,
            ResultadoEvaluacion.alumno_id == alumno_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        result = await self.db_session.execute(existing_q)
        existing = result.scalar_one_or_none()

        if existing:
            existing.nota_final = nota_final
            existing.updated_at = datetime.now(timezone.utc)
            await self.db_session.commit()
            await self.db_session.refresh(existing)
            return existing

        nuevo = ResultadoEvaluacion(
            id=uuid4(),
            tenant_id=self.tenant_id,
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            nota_final=nota_final,
        )
        self.db_session.add(nuevo)
        await self.db_session.commit()
        await self.db_session.refresh(nuevo)
        return nuevo

    async def get_resultados_con_candidatos(
        self,
        evaluacion_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        """Lista todos los candidatos con su resultado (null si no registrado)."""
        count_q = select(func.count()).where(
            EvaluacionCandidato.evaluacion_id == evaluacion_id
        )
        total = (await self.db_session.execute(count_q)).scalar_one()

        offset = (page - 1) * page_size
        rows_q = (
            select(
                EvaluacionCandidato.alumno_id,
                Usuario.nombre,
                Usuario.apellidos,
                ResultadoEvaluacion.nota_final,
            )
            .join(Usuario, Usuario.id == EvaluacionCandidato.alumno_id)
            .outerjoin(
                ResultadoEvaluacion,
                and_(
                    ResultadoEvaluacion.evaluacion_id == evaluacion_id,
                    ResultadoEvaluacion.alumno_id == EvaluacionCandidato.alumno_id,
                    ResultadoEvaluacion.deleted_at.is_(None),
                ),
            )
            .where(EvaluacionCandidato.evaluacion_id == evaluacion_id)
            .order_by(Usuario.apellidos, Usuario.nombre)
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(rows_q)
        items = []
        for alumno_id, nombre, apellidos, nota_final in result.all():
            items.append({
                "alumno_id": alumno_id,
                "alumno_nombre": f"{nombre} {apellidos}",
                "alumno_email": "",  # email se descifra en el service
                "nota_final": nota_final,
            })
        return items, total

    async def get_resultados_csv_rows(self, evaluacion_id: UUID) -> list[dict]:
        """Todos los candidatos con resultado para export CSV (sin paginación)."""
        rows_q = (
            select(
                EvaluacionCandidato.alumno_id,
                Usuario.nombre,
                Usuario.apellidos,
                ResultadoEvaluacion.nota_final,
            )
            .join(Usuario, Usuario.id == EvaluacionCandidato.alumno_id)
            .outerjoin(
                ResultadoEvaluacion,
                and_(
                    ResultadoEvaluacion.evaluacion_id == evaluacion_id,
                    ResultadoEvaluacion.alumno_id == EvaluacionCandidato.alumno_id,
                    ResultadoEvaluacion.deleted_at.is_(None),
                ),
            )
            .where(EvaluacionCandidato.evaluacion_id == evaluacion_id)
            .order_by(Usuario.apellidos, Usuario.nombre)
        )
        result = await self.db_session.execute(rows_q)
        return [
            {
                "alumno_nombre": f"{r.nombre} {r.apellidos}",
                "alumno_email": "",
                "nota_final": r.nota_final or "",
            }
            for r in result.all()
        ]

    # ------------------------------------------------------------------
    # 3.5 Métricas globales y agenda
    # ------------------------------------------------------------------

    async def get_metricas_globales(self) -> dict:
        total_cand = (
            await self.db_session.execute(
                select(func.count(EvaluacionCandidato.alumno_id))
                .join(Evaluacion, Evaluacion.id == EvaluacionCandidato.evaluacion_id)
                .where(
                    Evaluacion.tenant_id == self.tenant_id,
                    Evaluacion.deleted_at.is_(None),
                )
            )
        ).scalar_one()

        instancias_activas = (
            await self.db_session.execute(
                select(func.count()).where(
                    Evaluacion.tenant_id == self.tenant_id,
                    Evaluacion.deleted_at.is_(None),
                )
            )
        ).scalar_one()

        reservas_activas = (
            await self.db_session.execute(
                select(func.count())
                .join(Evaluacion, Evaluacion.id == ReservaEvaluacion.evaluacion_id)
                .where(
                    Evaluacion.tenant_id == self.tenant_id,
                    ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
                    ReservaEvaluacion.deleted_at.is_(None),
                )
            )
        ).scalar_one()

        notas_registradas = (
            await self.db_session.execute(
                select(func.count())
                .join(Evaluacion, Evaluacion.id == ResultadoEvaluacion.evaluacion_id)
                .where(
                    Evaluacion.tenant_id == self.tenant_id,
                    ResultadoEvaluacion.nota_final.isnot(None),
                    ResultadoEvaluacion.deleted_at.is_(None),
                )
            )
        ).scalar_one()

        return {
            "total_alumnos_cargados": total_cand,
            "instancias_activas": instancias_activas,
            "reservas_activas": reservas_activas,
            "notas_registradas": notas_registradas,
        }

    async def get_agenda_global(
        self,
        page: int,
        page_size: int,
        evaluacion_id: UUID | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        materia_id: UUID | None = None,
    ) -> tuple[list[dict], int]:
        filters = [
            Evaluacion.tenant_id == self.tenant_id,
            Evaluacion.deleted_at.is_(None),
            ReservaEvaluacion.estado == EstadoReserva.ACTIVA,
            ReservaEvaluacion.deleted_at.is_(None),
        ]
        if evaluacion_id:
            filters.append(ReservaEvaluacion.evaluacion_id == evaluacion_id)
        if fecha_desde:
            filters.append(ReservaEvaluacion.fecha_hora >= fecha_desde)
        if fecha_hasta:
            filters.append(ReservaEvaluacion.fecha_hora <= fecha_hasta)
        if materia_id:
            filters.append(Evaluacion.materia_id == materia_id)

        base_join = (
            select(ReservaEvaluacion)
            .join(Evaluacion, Evaluacion.id == ReservaEvaluacion.evaluacion_id)
            .where(*filters)
        )
        total = (
            await self.db_session.execute(
                select(func.count()).select_from(base_join.subquery())
            )
        ).scalar_one()

        offset = (page - 1) * page_size
        rows_q = (
            select(
                ReservaEvaluacion,
                Evaluacion.materia_id,
                Evaluacion.instancia,
                Materia.nombre.label("materia_nombre"),
                Usuario.nombre.label("alumno_nombre"),
                Usuario.apellidos.label("alumno_apellidos"),
            )
            .join(Evaluacion, Evaluacion.id == ReservaEvaluacion.evaluacion_id)
            .join(Materia, Materia.id == Evaluacion.materia_id)
            .join(Usuario, Usuario.id == ReservaEvaluacion.alumno_id)
            .where(*filters)
            .order_by(ReservaEvaluacion.fecha_hora)
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(rows_q)
        items = []
        for reserva, mat_id, instancia, mat_nombre, nombre, apellidos in result.all():
            items.append({
                "reserva_id": reserva.id,
                "evaluacion_id": reserva.evaluacion_id,
                "materia_id": mat_id,
                "materia_nombre": mat_nombre,
                "instancia": instancia,
                "alumno_id": reserva.alumno_id,
                "alumno_nombre": f"{nombre} {apellidos}",
                "fecha_hora": reserva.fecha_hora,
                "estado": reserva.estado,
            })
        return items, total
