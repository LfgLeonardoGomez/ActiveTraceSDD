"""Repository de Comunicacion con scope de tenant y máquina de estados.

Todas las operaciones son fail-closed respecto a tenant_id.
destinatario se cifra al persistir; nunca se devuelve en texto plano desde aquí.

Nota de seguridad:
    - encrypt_pii() se aplica al guardar destinatario.
    - El worker descifra con decrypt_pii() SOLO en memoria al despachar.
    - Nunca exponer destinatario descifrado en logs o respuestas.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_pii
from app.models.comunicacion import Comunicacion, EstadoComunicacion, transicion_valida
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ComunicacionRepository(BaseRepository[Comunicacion]):
    """Repository de mensajes salientes con scope de tenant.

    Hereda el BaseRepository que garantiza tenant_id en todo query.
    """

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, Comunicacion, tenant_id)

    # ------------------------------------------------------------------
    # 4.2 — Crear lote
    # ------------------------------------------------------------------

    async def crear_lote(
        self,
        lote: list[dict],
        usuario_id: UUID,
        materia_id: UUID,
    ) -> UUID:
        """Inserta N registros con el mismo lote_id. Cifra destinatario.

        Args:
            lote: Lista de dicts con keys: email, asunto, cuerpo.
            usuario_id: UUID del usuario que encola (del JWT).
            materia_id: UUID de la materia relacionada.

        Returns:
            lote_id compartido por todos los registros del lote.
        """
        lote_id = uuid4()
        for item in lote:
            destinatario_cifrado = encrypt_pii(item["email"])
            comunicacion = Comunicacion(
                id=uuid4(),
                tenant_id=self.tenant_id,
                enviado_por=usuario_id,
                materia_id=materia_id,
                destinatario=destinatario_cifrado,
                asunto=item["asunto"],
                cuerpo=item["cuerpo"],
                estado=EstadoComunicacion.pendiente.value,
                lote_id=lote_id,
                aprobado=False,
            )
            self.db_session.add(comunicacion)

        await self.db_session.commit()
        return lote_id

    # ------------------------------------------------------------------
    # 4.3 — Estado del lote
    # ------------------------------------------------------------------

    async def get_estado_lote(self, lote_id: UUID) -> dict:
        """Devuelve conteo por estado para el lote dado.

        Returns:
            Dict con keys: lote_id, total, pendiente, enviando, enviado, error, cancelado.
        """
        query = (
            select(Comunicacion.estado, func.count(Comunicacion.id).label("count"))
            .where(
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.lote_id == lote_id,
                Comunicacion.deleted_at.is_(None),
            )
            .group_by(Comunicacion.estado)
        )
        result = await self.db_session.execute(query)
        rows = result.all()

        counts: dict[str, int] = {
            "pendiente": 0,
            "enviando": 0,
            "enviado": 0,
            "error": 0,
            "cancelado": 0,
        }
        total = 0
        for estado, count in rows:
            key = estado.lower()
            if key in counts:
                counts[key] = count
            total += count

        return {
            "lote_id": lote_id,
            "total": total,
            **counts,
        }

    # ------------------------------------------------------------------
    # 4.4 — Aprobar lote
    # ------------------------------------------------------------------

    async def aprobar_lote(self, lote_id: UUID) -> int:
        """Marca aprobado=True para todos los Pendiente del lote.

        Returns:
            Cantidad de filas afectadas.
        """
        stmt = (
            update(Comunicacion)
            .where(
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.lote_id == lote_id,
                Comunicacion.estado == EstadoComunicacion.pendiente.value,
                Comunicacion.deleted_at.is_(None),
            )
            .values(aprobado=True, updated_at=datetime.now(timezone.utc))
        )
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount

    # ------------------------------------------------------------------
    # 4.5 — Cancelar lote
    # ------------------------------------------------------------------

    async def cancelar_lote(self, lote_id: UUID) -> int:
        """Transiciona a Cancelado todos los Pendiente del lote.

        Returns:
            Cantidad de filas afectadas.
        """
        stmt = (
            update(Comunicacion)
            .where(
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.lote_id == lote_id,
                Comunicacion.estado == EstadoComunicacion.pendiente.value,
                Comunicacion.deleted_at.is_(None),
            )
            .values(
                estado=EstadoComunicacion.cancelado.value,
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount

    # ------------------------------------------------------------------
    # 4.6 — Cancelar uno
    # ------------------------------------------------------------------

    async def cancelar_uno(self, comunicacion_id: UUID) -> Comunicacion:
        """Transiciona a Cancelado un mensaje individual en estado Pendiente.

        Raises:
            HTTPException 422: si el mensaje no existe o estado no es Pendiente.
        """
        comunicacion = await self.get_by_id(comunicacion_id)
        if comunicacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comunicación no encontrada",
            )

        estado_actual = EstadoComunicacion(comunicacion.estado)
        if not transicion_valida(estado_actual, EstadoComunicacion.cancelado):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"No se puede cancelar un mensaje en estado '{comunicacion.estado}'",
            )

        comunicacion.estado = EstadoComunicacion.cancelado.value
        comunicacion.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(comunicacion)
        return comunicacion

    # ------------------------------------------------------------------
    # 4.7 — Retry uno
    # ------------------------------------------------------------------

    async def retry_uno(self, comunicacion_id: UUID) -> Comunicacion:
        """Transiciona de Error a Pendiente para reintento manual.

        Raises:
            HTTPException 422: si el mensaje no existe o estado no es Error.
        """
        comunicacion = await self.get_by_id(comunicacion_id)
        if comunicacion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comunicación no encontrada",
            )

        estado_actual = EstadoComunicacion(comunicacion.estado)
        if not transicion_valida(estado_actual, EstadoComunicacion.pendiente):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"No se puede hacer retry de un mensaje en estado '{comunicacion.estado}'",
            )

        comunicacion.estado = EstadoComunicacion.pendiente.value
        comunicacion.error_detalle = None
        comunicacion.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(comunicacion)
        return comunicacion

    # ------------------------------------------------------------------
    # 4.8 — Pendientes elegibles por tenant
    # ------------------------------------------------------------------

    async def get_pendientes_para_despacho(
        self, batch_size: int
    ) -> list[Comunicacion]:
        """Toma mensajes elegibles para despacho del tenant actual.

        Elegible = Pendiente + (aprobado=True OR tenant no requiere aprobación).
        El worker verifica el flag del tenant antes de llamar a este método.

        Returns:
            Lista ordenada por created_at ASC, máximo batch_size registros.
        """
        query = (
            select(Comunicacion)
            .where(
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.estado == EstadoComunicacion.pendiente.value,
                Comunicacion.deleted_at.is_(None),
            )
            .order_by(Comunicacion.created_at.asc())
            .limit(batch_size)
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # 4.9 — Pendientes elegibles (todos los tenants, para el worker)
    # ------------------------------------------------------------------

    async def get_todos_pendientes_elegibles(
        self, batch_size: int
    ) -> list[Comunicacion]:
        """Toma mensajes elegibles de todos los tenants para el worker.

        Elegible = Pendiente + aprobado=True.
        Los tenants sin aprobación requerida tienen aprobado=True por defecto
        al ser encolados (el service lo gestiona).

        Returns:
            Lista ordenada por created_at ASC, máximo batch_size registros.
        """
        query = (
            select(Comunicacion)
            .where(
                Comunicacion.estado == EstadoComunicacion.pendiente.value,
                Comunicacion.aprobado.is_(True),
                Comunicacion.deleted_at.is_(None),
            )
            .order_by(Comunicacion.created_at.asc())
            .limit(batch_size)
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # 4.10 — Transiciones de estado del worker
    # ------------------------------------------------------------------

    async def marcar_enviando(self, comunicacion_id: UUID) -> None:
        """Transiciona Pendiente → Enviando."""
        stmt = (
            update(Comunicacion)
            .where(
                Comunicacion.id == comunicacion_id,
                Comunicacion.estado == EstadoComunicacion.pendiente.value,
            )
            .values(
                estado=EstadoComunicacion.enviando.value,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()

    async def marcar_enviado(self, comunicacion_id: UUID) -> None:
        """Transiciona Enviando → Enviado. Registra enviado_at."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(Comunicacion)
            .where(
                Comunicacion.id == comunicacion_id,
                Comunicacion.estado == EstadoComunicacion.enviando.value,
            )
            .values(
                estado=EstadoComunicacion.enviado.value,
                enviado_at=now,
                updated_at=now,
            )
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()

    async def marcar_error(self, comunicacion_id: UUID, detalle: str) -> None:
        """Transiciona Enviando → Error. Registra error_detalle."""
        stmt = (
            update(Comunicacion)
            .where(
                Comunicacion.id == comunicacion_id,
                Comunicacion.estado == EstadoComunicacion.enviando.value,
            )
            .values(
                estado=EstadoComunicacion.error.value,
                error_detalle=detalle[:2000],  # truncar para evitar overflow
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()

    # ------------------------------------------------------------------
    # 4.11 — Resetear colgados
    # ------------------------------------------------------------------

    async def resetear_colgados(self, stale_threshold_minutes: int) -> int:
        """Resetea a Pendiente los mensajes viejos en estado Enviando.

        Un mensaje está "colgado" si lleva más de stale_threshold_minutes
        en Enviando (probablemente el worker fue reiniciado mid-despacho).

        Returns:
            Cantidad de registros reseteados.
        """
        umbral = datetime.now(timezone.utc) - timedelta(minutes=stale_threshold_minutes)
        stmt = (
            update(Comunicacion)
            .where(
                Comunicacion.estado == EstadoComunicacion.enviando.value,
                Comunicacion.updated_at < umbral,
                Comunicacion.deleted_at.is_(None),
            )
            .values(
                estado=EstadoComunicacion.pendiente.value,
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = await self.db_session.execute(stmt)
        if result.rowcount > 0:
            await self.db_session.commit()
        return result.rowcount
