"""Servicio de gestión de encuentros y slots (C-13).

Reglas de negocio:
- Crear slot genera N instancias en una sola transacción (RN-13).
- Editar slot no afecta instancias existentes (RN-14).
- Soft-delete de slot cascada en soft-delete de instancias.
- Audit log en todas las operaciones de escritura.

No accede directamente a DB: delega todo a repositories.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.encuentros import (
    InstanciaEncuentroRepository,
    SlotEncuentroRepository,
)
from app.repositories.estructura import MateriaRepository
from app.schemas.encuentros import (
    BloqueHtmlParams,
    InstanciaCreate,
    InstanciaFilterParams,
    InstanciaRead,
    InstanciaUpdate,
    PaginatedInstanciaResponse,
    PaginatedSlotResponse,
    SlotCreate,
    SlotRead,
    SlotUpdate,
)


class EncuentroService:
    """Servicio de gestión de encuentros del tenant."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._repo_slot = SlotEncuentroRepository(db_session, tenant_id)
        self._repo_instancia = InstanciaEncuentroRepository(db_session, tenant_id)
        self._repo_materia = MateriaRepository(db_session, tenant_id)
        self._repo_audit = AuditLogRepository(db_session, tenant_id)

    async def _verify_materia_en_tenant(self, materia_id: UUID) -> None:
        """Verifica que la materia existe en el tenant.

        Raises:
            HTTPException 404: si no existe.
        """
        materia = await self._repo_materia.get_by_id(materia_id)
        if materia is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Materia no encontrada en el tenant",
            )

    async def _insert_audit_log(
        self,
        actor_id: UUID,
        accion: str,
        detalle: dict[str, Any],
        filas_afectadas: int = 0,
        materia_id: UUID | None = None,
    ) -> None:
        """Inserta registro de auditoría en la transacción activa."""
        entry = AuditLog(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            accion=accion,
            detalle=detalle,
            filas_afectadas=filas_afectadas,
            materia_id=materia_id,
        )
        await self._repo_audit.insert(entry)

    def _compute_fechas(self, fecha_inicio: date, dia_semana: int, cant_semanas: int) -> list[date]:
        """Calcula las fechas de las instancias a partir del slot.

        Args:
            fecha_inicio: fecha de inicio de la recurrencia.
            dia_semana: día de la semana (0=Lunes, 6=Domingo).
            cant_semanas: cantidad de semanas a generar.

        Returns:
            Lista de fechas, una por semana.
        """
        fechas = []
        # Ajustar fecha_inicio al día de la semana correcto
        delta_dias = (dia_semana - fecha_inicio.weekday()) % 7
        primera_fecha = fecha_inicio + timedelta(days=delta_dias)
        for i in range(cant_semanas):
            fechas.append(primera_fecha + timedelta(weeks=i))
        return fechas

    async def crear_slot(
        self,
        data: SlotCreate,
        actor_id: UUID,
    ) -> SlotEncuentro:
        """Crea un slot y genera N instancias en una sola transacción.

        Args:
            data: datos del slot.
            actor_id: UUID del usuario que crea el slot.

        Returns:
            Slot creado.

        Raises:
            HTTPException 404: si la materia no existe.
        """
        await self._verify_materia_en_tenant(data.materia_id)

        slot = await self._repo_slot.create(
            creador_id=actor_id,
            materia_id=data.materia_id,
            carrera_id=data.carrera_id,
            cohorte_id=data.cohorte_id,
            titulo=data.titulo,
            dia_semana=data.dia_semana,
            hora=data.hora,
            fecha_inicio=data.fecha_inicio,
            cant_semanas=data.cant_semanas,
            meet_url=data.meet_url,
            vigencia=data.vigencia,
        )

        fechas = self._compute_fechas(
            data.fecha_inicio,
            data.dia_semana,
            data.cant_semanas,
        )

        instancias = [
            InstanciaEncuentro(
                tenant_id=self.tenant_id,
                slot_id=slot.id,
                materia_id=data.materia_id,
                titulo=data.titulo,
                fecha=fecha,
                hora=data.hora,
                estado="Programado",
                meet_url=data.meet_url,
            )
            for fecha in fechas
        ]

        await self._repo_slot.bulk_create_instancias(instancias)
        await self.db_session.commit()

        await self._insert_audit_log(
            actor_id=actor_id,
            accion="ENCUENTRO_CREAR",
            detalle={
                "slot_id": str(slot.id),
                "materia_id": str(data.materia_id),
                "cant_semanas": data.cant_semanas,
                "cant_instancias": len(instancias),
            },
            filas_afectadas=len(instancias) + 1,
            materia_id=data.materia_id,
        )

        return slot

    async def crear_instancia_unica(
        self,
        data: InstanciaCreate,
        actor_id: UUID,
    ) -> InstanciaEncuentro:
        """Crea una instancia de encuentro independiente (sin slot).

        Args:
            data: datos de la instancia.
            actor_id: UUID del usuario que crea la instancia.

        Returns:
            Instancia creada.

        Raises:
            HTTPException 404: si la materia no existe.
        """
        await self._verify_materia_en_tenant(data.materia_id)

        instance = await self._repo_instancia.create(
            slot_id=data.slot_id,
            materia_id=data.materia_id,
            titulo=data.titulo,
            fecha=data.fecha,
            hora=data.hora,
            estado="Programado",
            meet_url=data.meet_url,
        )

        await self._insert_audit_log(
            actor_id=actor_id,
            accion="ENCUENTRO_CREAR",
            detalle={
                "instancia_id": str(instance.id),
                "materia_id": str(data.materia_id),
                "tipo": "unica",
            },
            filas_afectadas=1,
            materia_id=data.materia_id,
        )

        return instance

    async def listar_slots(
        self,
        materia_id: UUID | None,
        limit: int,
        offset: int,
    ) -> PaginatedSlotResponse:
        """Lista slots paginados."""
        items, total = await self._repo_slot.list_slots(
            materia_id=materia_id,
            limit=limit,
            offset=offset,
        )
        return PaginatedSlotResponse(
            items=[SlotRead.model_validate(s) for s in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def obtener_slot(self, slot_id: UUID) -> SlotEncuentro:
        """Obtiene un slot por ID.

        Raises:
            HTTPException 404: si no existe.
        """
        slot = await self._repo_slot.get_by_id(slot_id)
        if slot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot no encontrado",
            )
        return slot

    async def actualizar_slot(
        self,
        slot_id: UUID,
        data: SlotUpdate,
        actor_id: UUID,
    ) -> SlotEncuentro:
        """Actualiza un slot (no afecta instancias existentes).

        Raises:
            HTTPException 404: si no existe.
        """
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se proporcionaron campos para actualizar",
            )

        slot = await self._repo_slot.update(slot_id, update_data)
        if slot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot no encontrado",
            )

        await self._insert_audit_log(
            actor_id=actor_id,
            accion="ENCUENTRO_EDITAR",
            detalle={
                "slot_id": str(slot_id),
                "campos": list(update_data.keys()),
            },
            filas_afectadas=1,
            materia_id=slot.materia_id,
        )

        return slot

    async def eliminar_slot(
        self,
        slot_id: UUID,
        actor_id: UUID,
    ) -> None:
        """Soft-delete de slot y cascada a instancias.

        Raises:
            HTTPException 404: si no existe.
        """
        slot = await self._repo_slot.get_by_id(slot_id)
        if slot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot no encontrado",
            )

        await self._repo_slot.delete(slot_id)
        affected = await self._repo_instancia.soft_delete_by_slot_id(slot_id)
        await self.db_session.commit()

        await self._insert_audit_log(
            actor_id=actor_id,
            accion="ENCUENTRO_EDITAR",
            detalle={
                "slot_id": str(slot_id),
                "accion": "eliminar",
                "instancias_afectadas": affected,
            },
            filas_afectadas=affected + 1,
            materia_id=slot.materia_id,
        )

    async def editar_instancia(
        self,
        instancia_id: UUID,
        data: InstanciaUpdate,
        actor_id: UUID,
    ) -> InstanciaEncuentro:
        """Actualiza una instancia independiente del slot.

        Raises:
            HTTPException 404: si no existe.
        """
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se proporcionaron campos para actualizar",
            )

        instance = await self._repo_instancia.update_instancia(instancia_id, update_data)
        if instance is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instancia no encontrada",
            )

        await self.db_session.commit()

        await self._insert_audit_log(
            actor_id=actor_id,
            accion="ENCUENTRO_EDITAR",
            detalle={
                "instancia_id": str(instancia_id),
                "campos": list(update_data.keys()),
            },
            filas_afectadas=1,
            materia_id=instance.materia_id,
        )

        return instance

    async def listar_instancias(
        self,
        filters: InstanciaFilterParams,
        limit: int,
        offset: int,
    ) -> PaginatedInstanciaResponse:
        """Lista instancias paginadas con filtros."""
        items, total = await self._repo_instancia.list_instancias(
            materia_id=filters.materia_id,
            slot_id=filters.slot_id,
            estado=filters.estado,
            fecha_desde=filters.fecha_desde,
            fecha_hasta=filters.fecha_hasta,
            limit=limit,
            offset=offset,
        )
        return PaginatedInstanciaResponse(
            items=[InstanciaRead.model_validate(i) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def generar_bloque_html(
        self,
        params: BloqueHtmlParams,
    ) -> str:
        """Genera un bloque HTML o Markdown con las instancias de un slot/materia.

        Args:
            params: parámetros de filtro y formato.

        Returns:
            String con el bloque formateado.
        """
        items, _ = await self._repo_instancia.list_instancias(
            materia_id=params.materia_id,
            slot_id=params.slot_id,
            estado=None,
            fecha_desde=date.today(),
            fecha_hasta=None,
            limit=200,
            offset=0,
        )

        if not items:
            if params.formato == "markdown":
                return "No hay encuentros programados."
            return '<p class="encuentros-vacio">No hay encuentros programados.</p>'

        rows = []
        for inst in items:
            estado_cls = "encuentro-estado-" + inst.estado.lower()
            if params.formato == "markdown":
                rows.append(
                    f"| {inst.fecha} | {inst.hora} | {inst.titulo or '-'} | {inst.estado} |"
                )
            else:
                meet_link = ""
                if inst.meet_url:
                    meet_link = f'<a href="{inst.meet_url}" target="_blank">Meet</a>'
                rows.append(
                    f"<tr class='{estado_cls}'>"
                    f"<td>{inst.fecha}</td>"
                    f"<td>{inst.hora}</td>"
                    f"<td>{inst.titulo or ''}</td>"
                    f"<td>{meet_link}</td>"
                    f"<td>{inst.estado}</td>"
                    f"</tr>"
                )

        if params.formato == "markdown":
            header = "| Fecha | Hora | Título | Estado |"
            separator = "| --- | --- | --- | --- |"
            return "\n".join([header, separator] + rows)

        header = (
            "<thead><tr>"
            "<th>Fecha</th><th>Hora</th><th>Título</th><th>Meet</th><th>Estado</th>"
            "</tr></thead>"
        )
        body = "<tbody>" + "\n".join(rows) + "</tbody>"
        return (
            '<table class="encuentros-tabla">\n'
            f"{header}\n"
            f"{body}\n"
            "</table>"
        )
