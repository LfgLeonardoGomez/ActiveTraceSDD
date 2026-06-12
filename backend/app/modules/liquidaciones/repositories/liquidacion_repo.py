"""Repository de Liquidacion (C-18).

Guard de inmutabilidad (D3): lanza LiquidacionCerradaError en update/delete
sobre filas con estado=Cerrada. El guard vive en el repository, NO en el router,
para que ningún acceso interno pueda saltárselo.
"""

from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.liquidaciones.exceptions import LiquidacionCerradaError
from app.modules.liquidaciones.models.enums import EstadoLiquidacion
from app.modules.liquidaciones.models.liquidacion import Liquidacion
from app.repositories.base import BaseRepository


class LiquidacionRepository(BaseRepository[Liquidacion]):
    """Repository de Liquidacion con guard de inmutabilidad en estado=Cerrada."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, Liquidacion, tenant_id)

    async def update(self, obj_id: UUID, data: dict) -> Liquidacion | None:
        """Actualiza una liquidación.

        Raises:
            LiquidacionCerradaError: Si la fila tiene estado=Cerrada (D3).
        """
        instance = await self.get_by_id(obj_id)
        if instance is None:
            return None
        if instance.estado == EstadoLiquidacion.CERRADA:
            raise LiquidacionCerradaError(obj_id)
        return await super().update(obj_id, data)

    async def delete(self, obj_id: UUID) -> bool:
        """Soft delete de una liquidación.

        Raises:
            LiquidacionCerradaError: Si la fila tiene estado=Cerrada (D3).
        """
        instance = await self.get_by_id(obj_id)
        if instance is None:
            return False
        if instance.estado == EstadoLiquidacion.CERRADA:
            raise LiquidacionCerradaError(obj_id)
        return await super().delete(obj_id)

    async def get_by_cohorte_periodo(
        self, cohorte_id: UUID, periodo: str
    ) -> list[Liquidacion]:
        """Retorna todas las filas de un (cohorte_id, periodo) del tenant."""
        query = self._base_query().where(
            Liquidacion.cohorte_id == cohorte_id,
            Liquidacion.periodo == periodo,
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def periodo_esta_cerrado(self, cohorte_id: UUID, periodo: str) -> bool:
        """Verifica si el período ya tiene al menos una fila Cerrada."""
        query = (
            select(Liquidacion)
            .where(
                Liquidacion.tenant_id == self.tenant_id,
                Liquidacion.deleted_at.is_(None),
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.periodo == periodo,
                Liquidacion.estado == EstadoLiquidacion.CERRADA,
            )
            .limit(1)
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none() is not None

    async def bulk_create_cerradas(self, filas: list[dict]) -> list[Liquidacion]:
        """Inserta múltiples filas de liquidación con estado=Cerrada (para cierre).

        Cada dict debe incluir todos los campos obligatorios del modelo.
        NO aplica el guard de inmutabilidad (ya que estas son filas nuevas).
        """
        instancias = []
        for fila in filas:
            fila["tenant_id"] = self.tenant_id
            instancia = Liquidacion(**fila)
            self.db_session.add(instancia)
            instancias.append(instancia)
        await self.db_session.commit()
        for inst in instancias:
            await self.db_session.refresh(inst)
        return instancias

    async def list_historial(
        self,
        cohorte_id: UUID | None = None,
        usuario_id: UUID | None = None,
        desde_periodo: str | None = None,
        hasta_periodo: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Liquidacion], int]:
        """Historial paginado de liquidaciones Cerradas con filtros."""
        query = self._base_query().where(
            Liquidacion.estado == EstadoLiquidacion.CERRADA
        )
        if cohorte_id is not None:
            query = query.where(Liquidacion.cohorte_id == cohorte_id)
        if usuario_id is not None:
            query = query.where(Liquidacion.usuario_id == usuario_id)
        if desde_periodo is not None:
            query = query.where(Liquidacion.periodo >= desde_periodo)
        if hasta_periodo is not None:
            query = query.where(Liquidacion.periodo <= hasta_periodo)

        # Count total
        from sqlalchemy import func  # noqa: PLC0415
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        # Paginate
        query = (
            query
            .order_by(Liquidacion.periodo.desc(), Liquidacion.cohorte_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all()), total
