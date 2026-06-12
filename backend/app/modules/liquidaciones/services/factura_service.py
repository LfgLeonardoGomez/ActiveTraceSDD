"""Service de facturas docentes (C-18).

cargar, listar, abonar, soft_delete + audit FACTURA_*.
Valida que el usuario sea facturante antes de crear la factura.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.dependencies import CurrentUser
from app.models.user import Usuario
from app.modules.liquidaciones.audit_codes import LiquidacionesAuditAction
from app.modules.liquidaciones.exceptions import UsuarioNoFacturanteError
from app.modules.liquidaciones.repositories.factura_repo import FacturaRepository
from app.modules.liquidaciones.schemas.factura import (
    FacturaCreate,
    FacturaListFilter,
    FacturaRead,
)


class FacturaService:
    """Service de facturas de docentes facturantes."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._repo = FacturaRepository(db_session, tenant_id)

    async def cargar(self, data: FacturaCreate, actor: CurrentUser) -> FacturaRead:
        """Crea una factura, validando que el usuario sea facturante."""
        # Validar que el usuario pertenece al tenant y es facturante
        usuario = await self._get_usuario(data.usuario_id)
        if usuario is None or not usuario.facturador:
            raise UsuarioNoFacturanteError(data.usuario_id)

        now = datetime.now(timezone.utc)
        instancia = await self._repo.create(
            usuario_id=data.usuario_id,
            periodo=data.periodo,
            detalle=data.detalle,
            referencia_archivo=data.referencia_archivo,
            tamano_kb=data.tamano_kb,
            cargada_at=now,
        )
        await record_audit(
            self.db_session,
            actor_id=actor.real_actor_id,
            tenant_id=self.tenant_id,
            accion=LiquidacionesAuditAction.FACTURA_CARGAR,
            detalle={
                "factura_id": str(instancia.id),
                "usuario_id": str(data.usuario_id),
                "periodo": data.periodo,
            },
            filas_afectadas=1,
        )
        return FacturaRead.model_validate(instancia)

    async def listar(self, filtros: FacturaListFilter) -> tuple[list[FacturaRead], int]:
        """Lista facturas con filtros y paginación."""
        instancias, total = await self._repo.list_with_filters(
            usuario_id=filtros.usuario_id,
            estado=filtros.estado,
            desde_periodo=filtros.desde,
            hasta_periodo=filtros.hasta,
            q=filtros.q,
            page=filtros.page,
            page_size=filtros.page_size,
        )
        return [FacturaRead.model_validate(i) for i in instancias], total

    async def obtener(self, factura_id: UUID) -> FacturaRead | None:
        """Obtiene una factura por ID."""
        instancia = await self._repo.get_by_id(factura_id)
        if instancia is None:
            return None
        return FacturaRead.model_validate(instancia)

    async def abonar(self, factura_id: UUID, actor: CurrentUser) -> FacturaRead:
        """Transiciona una factura de Pendiente a Abonada.

        Raises:
            ValueError: Si la factura no existe.
            FacturaYaAbonadaError: Si ya está abonada.
        """
        instancia = await self._repo.transicionar_a_abonada(factura_id)
        await record_audit(
            self.db_session,
            actor_id=actor.real_actor_id,
            tenant_id=self.tenant_id,
            accion=LiquidacionesAuditAction.FACTURA_ABONAR,
            detalle={
                "factura_id": str(factura_id),
                "usuario_id": str(instancia.usuario_id),
                "periodo": instancia.periodo,
                "monto": None,
            },
            filas_afectadas=1,
        )
        return FacturaRead.model_validate(instancia)

    async def eliminar(self, factura_id: UUID, actor: CurrentUser) -> bool:
        """Soft delete de una factura."""
        instancia = await self._repo.get_by_id(factura_id)
        if instancia is None:
            return False
        eliminado = await self._repo.delete(factura_id)
        if eliminado:
            await record_audit(
                self.db_session,
                actor_id=actor.real_actor_id,
                tenant_id=self.tenant_id,
                accion=LiquidacionesAuditAction.FACTURA_DELETE,
                detalle={"factura_id": str(factura_id)},
                filas_afectadas=1,
            )
        return eliminado

    async def _get_usuario(self, usuario_id: UUID) -> Usuario | None:
        """Carga un usuario validando tenant scope."""
        result = await self.db_session.execute(
            select(Usuario).where(
                Usuario.id == usuario_id,
                Usuario.tenant_id == self.tenant_id,
                Usuario.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
