"""Service de cálculo de liquidación (C-18).

Implementa calcular_periodo() que, dada una (cohorte, periodo):
(a) Busca asignaciones activas en el período.
(b) Resuelve SalarioBase vigente por rol.
(c) Resuelve grupos por materia vía MateriaGrupoPlus.
(d) Resuelve SalarioPlus y aplica acumulación con tope (PA-23).
(e) Genera warnings para gaps de grilla.

Cálculo on-demand mientras estado=Abierta (D4).
"""

from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.dependencies import CurrentUser
from app.models.asignacion import Asignacion
from app.models.user import Usuario
from app.modules.liquidaciones.audit_codes import LiquidacionesAuditAction
from app.modules.liquidaciones.domain.calculadora_liquidacion import (
    aplicar_tope,
    calcular_total,
)
from app.modules.liquidaciones.domain.segmentador import segmentar
from app.modules.liquidaciones.models.enums import EstadoLiquidacion, RolDocente
from app.modules.liquidaciones.repositories.liquidacion_repo import LiquidacionRepository
from app.modules.liquidaciones.repositories.materia_grupo_plus_repo import (
    MateriaGrupoPlusRepository,
)
from app.modules.liquidaciones.repositories.salario_base_repo import SalarioBaseRepository
from app.modules.liquidaciones.repositories.salario_plus_repo import SalarioPlusRepository
from app.modules.liquidaciones.schemas.liquidacion import (
    LiquidacionFilaRead,
    LiquidacionPeriodoResponse,
    LiquidacionWarning,
    PlusDetalleItem,
    SegmentosLiquidacion,
)

# Roles que generan liquidación
_ROLES_LIQUIDABLES = {r.value for r in RolDocente}


class LiquidacionCalcService:
    """Service de cálculo de liquidación de un período."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._liq_repo = LiquidacionRepository(db_session, tenant_id)
        self._sb_repo = SalarioBaseRepository(db_session, tenant_id)
        self._sp_repo = SalarioPlusRepository(db_session, tenant_id)
        self._mgp_repo = MateriaGrupoPlusRepository(db_session, tenant_id)

    async def calcular_periodo(
        self,
        cohorte_id: UUID,
        periodo: str,
        actor: CurrentUser,
    ) -> LiquidacionPeriodoResponse:
        """Calcula o retorna la liquidación del período.

        Si el período está Cerrado: retorna snapshot persistido.
        Si está Abierto: recalcula on-demand sin persistir (D4).
        """
        # Verificar si ya está cerrado
        ya_cerrado = await self._liq_repo.periodo_esta_cerrado(cohorte_id, periodo)

        if ya_cerrado:
            return await self._calcular_desde_snapshot(cohorte_id, periodo, actor)
        else:
            return await self._calcular_on_demand(cohorte_id, periodo, actor)

    async def _calcular_desde_snapshot(
        self, cohorte_id: UUID, periodo: str, actor: CurrentUser
    ) -> LiquidacionPeriodoResponse:
        """Retorna la liquidación cerrada desde las filas persistidas."""
        filas_orm = await self._liq_repo.get_by_cohorte_periodo(cohorte_id, periodo)

        cerrada_at = filas_orm[0].cerrada_at if filas_orm else None
        cerrada_por = filas_orm[0].cerrada_por_usuario_id if filas_orm else None

        filas_dto = []
        for fila in filas_orm:
            plus_detalle = []
            if fila.detalle_plus:
                import json  # noqa: PLC0415
                try:
                    raw = json.loads(fila.detalle_plus)
                    plus_detalle = [PlusDetalleItem(**item) for item in raw]
                except Exception:
                    pass
            filas_dto.append(
                LiquidacionFilaRead(
                    id=fila.id,
                    usuario_id=fila.usuario_id,
                    rol=fila.rol,
                    monto_base=fila.monto_base,
                    monto_plus=fila.monto_plus,
                    total=fila.total,
                    es_nexo=fila.es_nexo,
                    excluido_por_factura=fila.excluido_por_factura,
                    estado=fila.estado,
                    cerrada_at=fila.cerrada_at,
                    cerrada_por_usuario_id=fila.cerrada_por_usuario_id,
                    plus_detalle=plus_detalle,
                )
            )

        resultado_seg = segmentar(filas_dto)

        await record_audit(
            self.db_session,
            actor_id=actor.real_actor_id,
            tenant_id=self.tenant_id,
            accion=LiquidacionesAuditAction.LIQUIDACION_CALCULAR,
            detalle={
                "cohorte_id": str(cohorte_id),
                "periodo": periodo,
                "modo": "cerrada",
                "total_filas": len(filas_dto),
            },
        )

        return LiquidacionPeriodoResponse(
            cohorte_id=cohorte_id,
            periodo=periodo,
            estado=EstadoLiquidacion.CERRADA,
            cerrada_at=cerrada_at,
            cerrada_por_usuario_id=cerrada_por,
            segmentos=SegmentosLiquidacion(
                general=resultado_seg.general,
                nexo=resultado_seg.nexo,
                facturantes=resultado_seg.facturantes,
            ),
            total_sin_factura=resultado_seg.total_sin_factura,
            total_con_factura=resultado_seg.total_con_factura,
            warnings=[],
        )

    async def _calcular_on_demand(
        self, cohorte_id: UUID, periodo: str, actor: CurrentUser
    ) -> LiquidacionPeriodoResponse:
        """Calcula la liquidación on-demand a partir de asignaciones y grilla vigente."""
        warnings: list[LiquidacionWarning] = []

        # 1. Buscar asignaciones activas en el período para esta cohorte
        asignaciones = await self._get_asignaciones_activas(cohorte_id, periodo)

        if not asignaciones:
            await record_audit(
                self.db_session,
                actor_id=actor.real_actor_id,
                tenant_id=self.tenant_id,
                accion=LiquidacionesAuditAction.LIQUIDACION_CALCULAR,
                detalle={
                    "cohorte_id": str(cohorte_id),
                    "periodo": periodo,
                    "modo": "abierta",
                    "total_filas": 0,
                },
            )
            return LiquidacionPeriodoResponse(
                cohorte_id=cohorte_id,
                periodo=periodo,
                estado=EstadoLiquidacion.ABIERTA,
                segmentos=SegmentosLiquidacion(),
                total_sin_factura=Decimal("0"),
                total_con_factura=Decimal("0"),
                warnings=[],
            )

        # 2. Obtener usuarios involucrados
        usuario_ids = list({a.usuario_id for a in asignaciones})
        usuarios_dict = await self._get_usuarios(usuario_ids)

        # 3. Agrupar asignaciones por (usuario_id, rol)
        grupo_asig: dict[tuple, list] = defaultdict(list)
        for asig in asignaciones:
            grupo_asig[(asig.usuario_id, asig.rol)].append(asig)

        filas: list[LiquidacionFilaRead] = []

        for (usuario_id, rol), asigs in grupo_asig.items():
            if rol not in _ROLES_LIQUIDABLES:
                continue

            usuario = usuarios_dict.get(usuario_id)
            es_facturante = usuario.facturador is True if usuario else False

            # 4. Resolver SalarioBase vigente
            sb = await self._sb_repo.find_vigente(rol, periodo)
            if sb is None:
                warnings.append(
                    LiquidacionWarning(
                        usuario_id=usuario_id,
                        rol=rol,
                        motivo="SIN_BASE_VIGENTE",
                    )
                )
                continue

            # 5. Resolver grupos de materias y acumular plus
            # Agrupar asignaciones del usuario en este rol por materia
            materia_ids = list({a.materia_id for a in asigs if a.materia_id is not None})

            # Mapear materia → grupo
            grupos_comisiones: dict[str, int] = defaultdict(int)
            for materia_id in materia_ids:
                grupo = await self._mgp_repo.find_grupo_vigente(materia_id, periodo)
                if grupo:
                    # Contar comisiones del usuario en esta materia en el período
                    count = sum(1 for a in asigs if a.materia_id == materia_id)
                    grupos_comisiones[grupo] += count

            # 6. Resolver SalarioPlus y calcular plus acumulado
            plus_detalle: list[PlusDetalleItem] = []
            plus_totales: list[Decimal] = []

            for grupo, n_comisiones in grupos_comisiones.items():
                sp = await self._sp_repo.find_vigente(grupo, rol, periodo)
                if sp is None:
                    continue
                n_efectivo = aplicar_tope(n_comisiones, sp.tope_acumulacion)
                subtotal = sp.monto * Decimal(str(n_efectivo))
                plus_detalle.append(
                    PlusDetalleItem(
                        grupo=grupo,
                        monto_unitario=sp.monto,
                        n_comisiones_detectadas=n_comisiones,
                        n_comisiones_acumuladas=n_efectivo,
                        tope_acumulacion=sp.tope_acumulacion,
                        subtotal=subtotal,
                    )
                )
                plus_totales.append(subtotal)

            monto_plus = sum(plus_totales, Decimal("0"))
            total = calcular_total(sb.monto, plus_totales)

            filas.append(
                LiquidacionFilaRead(
                    usuario_id=usuario_id,
                    rol=rol,
                    monto_base=sb.monto,
                    monto_plus=monto_plus,
                    total=total,
                    es_nexo=(rol == RolDocente.NEXO),
                    excluido_por_factura=es_facturante,
                    estado=EstadoLiquidacion.ABIERTA,
                    plus_detalle=plus_detalle,
                )
            )

        # 7. Segmentar
        resultado_seg = segmentar(filas)

        await record_audit(
            self.db_session,
            actor_id=actor.real_actor_id,
            tenant_id=self.tenant_id,
            accion=LiquidacionesAuditAction.LIQUIDACION_CALCULAR,
            detalle={
                "cohorte_id": str(cohorte_id),
                "periodo": periodo,
                "modo": "abierta",
                "total_filas": len(filas),
            },
        )

        return LiquidacionPeriodoResponse(
            cohorte_id=cohorte_id,
            periodo=periodo,
            estado=EstadoLiquidacion.ABIERTA,
            segmentos=SegmentosLiquidacion(
                general=resultado_seg.general,
                nexo=resultado_seg.nexo,
                facturantes=resultado_seg.facturantes,
            ),
            total_sin_factura=resultado_seg.total_sin_factura,
            total_con_factura=resultado_seg.total_con_factura,
            warnings=warnings,
        )

    async def _get_asignaciones_activas(
        self, cohorte_id: UUID, periodo: str
    ) -> list[Asignacion]:
        """Retorna asignaciones del tenant scoped a la cohorte y vigentes en el período."""
        import calendar  # noqa: PLC0415
        from datetime import date  # noqa: PLC0415

        year, month = int(periodo[:4]), int(periodo[5:7])
        primer_dia = date(year, month, 1)
        ultimo_dia = date(year, month, calendar.monthrange(year, month)[1])

        from sqlalchemy import or_  # noqa: PLC0415

        query = (
            select(Asignacion)
            .where(
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.cohorte_id == cohorte_id,
                Asignacion.rol.in_(_ROLES_LIQUIDABLES),
                Asignacion.desde <= ultimo_dia,
                or_(
                    Asignacion.hasta.is_(None),
                    Asignacion.hasta >= primer_dia,
                ),
            )
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def _get_usuarios(self, usuario_ids: list[UUID]) -> dict[UUID, Usuario]:
        """Carga los usuarios por IDs en batch."""
        if not usuario_ids:
            return {}
        query = select(Usuario).where(
            Usuario.tenant_id == self.tenant_id,
            Usuario.id.in_(usuario_ids),
        )
        result = await self.db_session.execute(query)
        return {u.id: u for u in result.scalars().all()}
