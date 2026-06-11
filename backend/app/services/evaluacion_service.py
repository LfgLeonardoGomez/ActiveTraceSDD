"""Service de evaluaciones y coloquios (C-14).

Orquesta queries del repository, valida reglas de negocio y aplica
lógica de dominio: cupo, candidatos, state machine de reservas.

Reglas duras:
- tenant_id y usuario_id SIEMPRE del JWT (PermissionContext/CurrentUser).
- Nunca lógica de negocio en Routers.
- Nunca acceso directo a DB desde este Service (siempre vía Repository).
"""

from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.evaluacion_repository import EvaluacionRepository
from app.schemas.evaluacion import (
    AgendaResponseSchema,
    AgendaItemSchema,
    CandidatosImportResponseSchema,
    EstadoReserva,
    EvaluacionResponseSchema,
    MetricasColoquiosSchema,
    ResultadoResponseSchema,
    ResultadosListResponseSchema,
    ReservaResponseSchema,
    ReservasListResponseSchema,
    TipoEvaluacion,
)

from datetime import datetime


class EvaluacionService:
    """Service de evaluaciones: lógica de negocio de convocatorias y coloquios."""

    def __init__(
        self,
        db_session: AsyncSession,
        tenant_id: UUID,
        usuario_id: UUID,
    ) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.usuario_id = usuario_id
        self._repo = EvaluacionRepository(db_session, tenant_id)

    def _paginas(self, total: int, page_size: int) -> int:
        if page_size <= 0:
            return 0
        return ceil(total / page_size) if total > 0 else 0

    # ------------------------------------------------------------------
    # 4.1 Convocatorias
    # ------------------------------------------------------------------

    async def crear_convocatoria(self, data: dict) -> EvaluacionResponseSchema:
        evaluacion = await self._repo.create(data)
        return EvaluacionResponseSchema(
            id=evaluacion.id,
            materia_id=evaluacion.materia_id,
            cohorte_id=evaluacion.cohorte_id,
            tipo=TipoEvaluacion(evaluacion.tipo),
            instancia=evaluacion.instancia,
            dias_disponibles=evaluacion.dias_disponibles,
            cupo_por_dia=evaluacion.cupo_por_dia,
            convocados=0,
            reservas_activas=0,
            cupos_libres_por_dia=evaluacion.cupo_por_dia,
            created_at=evaluacion.created_at,
        )

    async def importar_candidatos(
        self, evaluacion_id: UUID, alumno_ids: list[UUID]
    ) -> CandidatosImportResponseSchema:
        evaluacion = await self._repo.get_by_id(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )
        total = await self._repo.import_candidatos(evaluacion_id, alumno_ids)
        return CandidatosImportResponseSchema(total_candidatos=total)

    async def list_convocatorias(
        self, page: int, page_size: int
    ) -> dict:
        items_raw, total = await self._repo.list_with_metrics(page, page_size)
        items = [
            EvaluacionResponseSchema(
                id=r["id"],
                materia_id=r["materia_id"],
                cohorte_id=r["cohorte_id"],
                tipo=TipoEvaluacion(r["tipo"]),
                instancia=r["instancia"],
                dias_disponibles=r["dias_disponibles"],
                cupo_por_dia=r["cupo_por_dia"],
                convocados=r["convocados"],
                reservas_activas=r["reservas_activas"],
                cupos_libres_por_dia=r["cupos_libres_por_dia"],
                created_at=r["created_at"],
            )
            for r in items_raw
        ]
        return {
            "items": items,
            "total": total,
            "page": page,
            "pages": self._paginas(total, page_size),
        }

    async def update_convocatoria(
        self, evaluacion_id: UUID, data: dict
    ) -> EvaluacionResponseSchema:
        # Eliminar None values — solo actualizar los campos enviados
        clean_data = {k: v for k, v in data.items() if v is not None}
        evaluacion = await self._repo.update(evaluacion_id, clean_data)
        if evaluacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )
        # Recalcular métricas tras update
        items_raw, _ = await self._repo.list_with_metrics(1, 1)
        # Buscar en la lista
        ev_data = next(
            (r for r in items_raw if r["id"] == evaluacion_id), None
        )
        if ev_data:
            return EvaluacionResponseSchema(**ev_data)
        return EvaluacionResponseSchema(
            id=evaluacion.id,
            materia_id=evaluacion.materia_id,
            cohorte_id=evaluacion.cohorte_id,
            tipo=TipoEvaluacion(evaluacion.tipo),
            instancia=evaluacion.instancia,
            dias_disponibles=evaluacion.dias_disponibles,
            cupo_por_dia=evaluacion.cupo_por_dia,
            convocados=0,
            reservas_activas=0,
            cupos_libres_por_dia=evaluacion.cupo_por_dia,
            created_at=evaluacion.created_at,
        )

    # ------------------------------------------------------------------
    # 4.2 Crear reserva con validación de cupo
    # ------------------------------------------------------------------

    async def crear_reserva(
        self, evaluacion_id: UUID, alumno_id: UUID, fecha_hora: datetime
    ) -> ReservaResponseSchema:
        evaluacion = await self._repo.get_by_id(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )

        # Verificar que el alumno está en el padrón de candidatos
        if not await self._repo.is_candidato(evaluacion_id, alumno_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El alumno no está habilitado para esta convocatoria",
            )

        # Verificar reserva duplicada activa
        reserva_existente = await self._repo.get_reserva_activa_del_alumno(
            evaluacion_id, alumno_id
        )
        if reserva_existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="reserva_duplicada",
            )

        # Validar cupo con SELECT FOR UPDATE (D3)
        ocupadas = await self._repo.count_reservas_activas_en_dia(
            evaluacion_id, fecha_hora
        )
        if ocupadas >= evaluacion.cupo_por_dia:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="sin_cupo_disponible",
            )

        reserva = await self._repo.create_reserva(evaluacion_id, alumno_id, fecha_hora)
        return ReservaResponseSchema(
            id=reserva.id,
            evaluacion_id=reserva.evaluacion_id,
            alumno_id=reserva.alumno_id,
            alumno_nombre="",  # el router puede enriquecer si necesita
            fecha_hora=reserva.fecha_hora,
            estado=EstadoReserva(reserva.estado),
            created_at=reserva.created_at,
        )

    # ------------------------------------------------------------------
    # 4.3 Cancelar reserva
    # ------------------------------------------------------------------

    async def cancelar_reserva(
        self,
        evaluacion_id: UUID,
        reserva_id: UUID,
        solicitante_id: UUID,
        puede_gestionar: bool,
    ) -> ReservaResponseSchema:
        reserva = await self._repo.get_reserva_by_id(reserva_id)
        if reserva is None or reserva.evaluacion_id != evaluacion_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada",
            )

        # Verificar pertenencia si no es coordinador/admin
        if not puede_gestionar and reserva.alumno_id != solicitante_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No podés cancelar la reserva de otro alumno",
            )

        if reserva.estado == EstadoReserva.CANCELADA:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="reserva_ya_cancelada",
            )

        reserva = await self._repo.cancel_reserva(reserva)
        return ReservaResponseSchema(
            id=reserva.id,
            evaluacion_id=reserva.evaluacion_id,
            alumno_id=reserva.alumno_id,
            alumno_nombre="",
            fecha_hora=reserva.fecha_hora,
            estado=EstadoReserva(reserva.estado),
            created_at=reserva.created_at,
        )

    # ------------------------------------------------------------------
    # 4.4 Listar reservas, registrar resultado, listar resultados
    # ------------------------------------------------------------------

    async def get_reservas(
        self, evaluacion_id: UUID, page: int, page_size: int
    ) -> ReservasListResponseSchema:
        evaluacion = await self._repo.get_by_id(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )
        items_raw, total = await self._repo.get_reservas(evaluacion_id, page, page_size)
        items = [
            ReservaResponseSchema(
                id=r["id"],
                evaluacion_id=r["evaluacion_id"],
                alumno_id=r["alumno_id"],
                alumno_nombre=r["alumno_nombre"],
                fecha_hora=r["fecha_hora"],
                estado=EstadoReserva(r["estado"]),
                created_at=r["created_at"],
            )
            for r in items_raw
        ]
        return ReservasListResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )

    async def registrar_resultado(
        self, evaluacion_id: UUID, alumno_id: UUID, nota_final: str
    ) -> ResultadoResponseSchema:
        evaluacion = await self._repo.get_by_id(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )
        if not await self._repo.is_candidato(evaluacion_id, alumno_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El alumno no pertenece a esta convocatoria",
            )
        await self._repo.upsert_resultado(evaluacion_id, alumno_id, nota_final)
        return ResultadoResponseSchema(
            alumno_id=alumno_id,
            alumno_nombre="",
            alumno_email="",
            nota_final=nota_final,
        )

    async def get_resultados(
        self, evaluacion_id: UUID, page: int, page_size: int
    ) -> ResultadosListResponseSchema:
        evaluacion = await self._repo.get_by_id(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocatoria no encontrada",
            )
        items_raw, total = await self._repo.get_resultados_con_candidatos(
            evaluacion_id, page, page_size
        )
        items = [
            ResultadoResponseSchema(
                alumno_id=r["alumno_id"],
                alumno_nombre=r["alumno_nombre"],
                alumno_email=r["alumno_email"],
                nota_final=r["nota_final"],
            )
            for r in items_raw
        ]
        return ResultadosListResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )

    # ------------------------------------------------------------------
    # 4.5 Métricas globales y agenda
    # ------------------------------------------------------------------

    async def get_metricas_globales(self) -> MetricasColoquiosSchema:
        data = await self._repo.get_metricas_globales()
        return MetricasColoquiosSchema(**data)

    async def get_agenda_global(
        self,
        page: int,
        page_size: int,
        evaluacion_id: UUID | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        materia_id: UUID | None = None,
    ) -> AgendaResponseSchema:
        items_raw, total = await self._repo.get_agenda_global(
            page=page,
            page_size=page_size,
            evaluacion_id=evaluacion_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            materia_id=materia_id,
        )
        items = [
            AgendaItemSchema(
                reserva_id=r["reserva_id"],
                evaluacion_id=r["evaluacion_id"],
                materia_id=r["materia_id"],
                materia_nombre=r["materia_nombre"],
                instancia=r["instancia"],
                alumno_id=r["alumno_id"],
                alumno_nombre=r["alumno_nombre"],
                fecha_hora=r["fecha_hora"],
                estado=EstadoReserva(r["estado"]),
            )
            for r in items_raw
        ]
        return AgendaResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )
