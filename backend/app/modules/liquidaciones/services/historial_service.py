"""Service de historial de liquidaciones cerradas (C-18)."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.liquidaciones.repositories.liquidacion_repo import LiquidacionRepository
from app.modules.liquidaciones.schemas.liquidacion import (
    HistorialPeriodoItem,
    HistorialResponse,
)


class HistorialService:
    """Service de historial de liquidaciones cerradas con paginación."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._repo = LiquidacionRepository(db_session, tenant_id)

    async def listar_historial(
        self,
        cohorte_id: UUID | None = None,
        usuario_id: UUID | None = None,
        desde_periodo: str | None = None,
        hasta_periodo: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> HistorialResponse:
        """Lista períodos cerrados con aggregados y filtros."""
        filas, total = await self._repo.list_historial(
            cohorte_id=cohorte_id,
            usuario_id=usuario_id,
            desde_periodo=desde_periodo,
            hasta_periodo=hasta_periodo,
            page=page,
            page_size=page_size,
        )

        # Agrupar por (cohorte_id, periodo) para calcular aggregados
        from collections import defaultdict  # noqa: PLC0415

        periodos: dict[tuple, dict] = defaultdict(lambda: {
            "total_filas": 0,
            "total_sin_factura": Decimal("0"),
            "total_con_factura": Decimal("0"),
            "cerrada_at": None,
            "cerrada_por_usuario_id": None,
        })

        for fila in filas:
            key = (fila.cohorte_id, fila.periodo)
            periodos[key]["total_filas"] += 1
            if fila.excluido_por_factura:
                periodos[key]["total_con_factura"] += fila.total
            else:
                periodos[key]["total_sin_factura"] += fila.total
            if periodos[key]["cerrada_at"] is None:
                periodos[key]["cerrada_at"] = fila.cerrada_at
                periodos[key]["cerrada_por_usuario_id"] = fila.cerrada_por_usuario_id

        items = [
            HistorialPeriodoItem(
                cohorte_id=key[0],
                periodo=key[1],
                total_filas=datos["total_filas"],
                total_sin_factura=datos["total_sin_factura"],
                total_con_factura=datos["total_con_factura"],
                cerrada_at=datos["cerrada_at"],
                cerrada_por_usuario_id=datos["cerrada_por_usuario_id"],
            )
            for key, datos in periodos.items()
        ]

        return HistorialResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
