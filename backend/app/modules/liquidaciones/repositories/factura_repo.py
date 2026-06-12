"""Repository de Factura (C-18).

Scope: tenant_id obligatorio.
Operaciones: create/list/find_by_id/transicionar_a_abonada/soft_delete.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.liquidaciones.exceptions import FacturaYaAbonadaError
from app.modules.liquidaciones.models.enums import EstadoFactura
from app.modules.liquidaciones.models.factura import Factura
from app.repositories.base import BaseRepository


class FacturaRepository(BaseRepository[Factura]):
    """Repository de Factura con scope de tenant."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, Factura, tenant_id)

    async def transicionar_a_abonada(self, factura_id: UUID) -> Factura:
        """Transiciona una factura de Pendiente a Abonada.

        Raises:
            ValueError: Si la factura no existe.
            FacturaYaAbonadaError: Si la factura ya está en estado Abonada.
        """
        instance = await self.get_by_id(factura_id)
        if instance is None:
            raise ValueError(f"Factura {factura_id} no encontrada")
        if instance.estado == EstadoFactura.ABONADA:
            raise FacturaYaAbonadaError(factura_id)
        now = datetime.now(timezone.utc)
        return await self.update(
            factura_id,
            {"estado": EstadoFactura.ABONADA, "abonada_at": now},
        )

    async def list_with_filters(
        self,
        usuario_id: UUID | None = None,
        estado: str | None = None,
        desde_periodo: str | None = None,
        hasta_periodo: str | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Factura], int]:
        """Lista facturas con filtros y paginación."""
        query = self._base_query()

        if usuario_id is not None:
            query = query.where(Factura.usuario_id == usuario_id)
        if estado is not None:
            query = query.where(Factura.estado == estado)
        if desde_periodo is not None:
            query = query.where(Factura.periodo >= desde_periodo)
        if hasta_periodo is not None:
            query = query.where(Factura.periodo <= hasta_periodo)
        if q is not None:
            query = query.where(Factura.detalle.ilike(f"%{q}%"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        # Paginate
        query = (
            query
            .order_by(Factura.cargada_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all()), total
