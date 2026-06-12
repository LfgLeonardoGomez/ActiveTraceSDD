"""Service de cierre de liquidación (C-18).

cerrar_periodo(): persiste filas con estado=Cerrada, rechaza doble cierre (D3).
"""

import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.dependencies import CurrentUser
from app.modules.liquidaciones.audit_codes import LiquidacionesAuditAction
from app.modules.liquidaciones.exceptions import PeriodoYaCerradoError
from app.modules.liquidaciones.models.enums import EstadoLiquidacion
from app.modules.liquidaciones.repositories.liquidacion_repo import LiquidacionRepository
from app.modules.liquidaciones.schemas.liquidacion import LiquidacionPeriodoResponse
from app.modules.liquidaciones.services.liquidacion_calc_service import LiquidacionCalcService


class LiquidacionCierreService:
    """Service de cierre inmutable de un período."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._liq_repo = LiquidacionRepository(db_session, tenant_id)
        self._calc_service = LiquidacionCalcService(db_session, tenant_id)

    async def cerrar_periodo(
        self,
        cohorte_id: UUID,
        periodo: str,
        actor: CurrentUser,
    ) -> LiquidacionPeriodoResponse:
        """Cierra un período calculando y persistiendo sus filas como Cerradas.

        (a) Verifica que el período no esté ya cerrado.
        (b) Ejecuta el cálculo on-demand.
        (c) Persiste filas con estado=Cerrada y snapshot de excluido_por_factura.
        (d) Audita LIQUIDACION_CERRAR.

        Raises:
            PeriodoYaCerradoError: Si ya existe una fila Cerrada para este período.
        """
        # (a) Verificar doble cierre
        if await self._liq_repo.periodo_esta_cerrado(cohorte_id, periodo):
            raise PeriodoYaCerradoError(cohorte_id, periodo)

        # (b) Calcular on-demand
        calculo = await self._calc_service._calcular_on_demand(cohorte_id, periodo, actor)

        # Recolectar todas las filas de los tres segmentos
        todas_filas = (
            calculo.segmentos.general
            + calculo.segmentos.nexo
            + calculo.segmentos.facturantes
        )

        now = datetime.now(timezone.utc)

        # (c) Persistir como Cerradas
        filas_a_persistir = []
        for fila in todas_filas:
            plus_json = json.dumps(
                [item.model_dump(mode="json") for item in fila.plus_detalle]
            )
            filas_a_persistir.append(
                {
                    "cohorte_id": cohorte_id,
                    "periodo": periodo,
                    "usuario_id": fila.usuario_id,
                    "rol": fila.rol,
                    "monto_base": fila.monto_base,
                    "monto_plus": fila.monto_plus,
                    "total": fila.total,
                    "es_nexo": fila.es_nexo,
                    "excluido_por_factura": fila.excluido_por_factura,
                    "estado": EstadoLiquidacion.CERRADA,
                    "cerrada_at": now,
                    "cerrada_por_usuario_id": actor.real_actor_id,
                    "detalle_plus": plus_json,
                    "cargada_at": now,  # no es campo de Liquidacion, se ignorará
                }
            )

        persistidas = []
        if filas_a_persistir:
            # Eliminar campo que no existe en Liquidacion
            for f in filas_a_persistir:
                f.pop("cargada_at", None)
            persistidas = await self._liq_repo.bulk_create_cerradas(filas_a_persistir)

        # (d) Auditar
        await record_audit(
            self.db_session,
            actor_id=actor.real_actor_id,
            tenant_id=self.tenant_id,
            accion=LiquidacionesAuditAction.LIQUIDACION_CERRAR,
            detalle={
                "cohorte_id": str(cohorte_id),
                "periodo": periodo,
                "total_filas": len(persistidas),
                "total_sin_factura": str(calculo.total_sin_factura),
                "total_con_factura": str(calculo.total_con_factura),
            },
            filas_afectadas=len(persistidas),
        )

        # Retornar respuesta con estado Cerrada
        from app.modules.liquidaciones.schemas.liquidacion import (  # noqa: PLC0415
            LiquidacionFilaRead,
            SegmentosLiquidacion,
        )

        # Re-leer desde snapshot para devolver IDs persistidos
        return await self._calc_service._calcular_desde_snapshot(cohorte_id, periodo, actor)
