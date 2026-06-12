"""Service de SalarioBase (C-18).

CRUD + validación de overlap + audit SALARIO_BASE_MODIFICAR.
Flujo: Router → Service → Repository → Model.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.dependencies import CurrentUser
from app.modules.liquidaciones.audit_codes import LiquidacionesAuditAction
from app.modules.liquidaciones.repositories.salario_base_repo import SalarioBaseRepository
from app.modules.liquidaciones.models.salario_base import SalarioBase
from app.modules.liquidaciones.schemas.salario_base import (
    SalarioBaseCreate,
    SalarioBaseRead,
    SalarioBaseUpdate,
)


class SalarioBaseService:
    """Service de SalarioBase con validación de overlap y auditoría."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._repo = SalarioBaseRepository(db_session, tenant_id)

    async def crear(self, data: SalarioBaseCreate, actor: CurrentUser) -> SalarioBaseRead:
        """Crea un SalarioBase con validación de no-solapamiento."""
        instancia = await self._repo.create_with_overlap_check(
            rol=data.rol,
            monto=data.monto,
            desde=data.desde,
            hasta=data.hasta,
        )
        await record_audit(
            self.db_session,
            actor_id=actor.real_actor_id,
            tenant_id=self.tenant_id,
            accion=LiquidacionesAuditAction.SALARIO_BASE_CREAR,
            detalle={
                "operacion": "CREATE",
                "after": {
                    "id": str(instancia.id),
                    "rol": instancia.rol,
                    "monto": str(instancia.monto),
                    "desde": str(instancia.desde),
                    "hasta": str(instancia.hasta) if instancia.hasta else None,
                },
            },
            filas_afectadas=1,
        )
        return SalarioBaseRead.model_validate(instancia)

    async def actualizar(
        self, obj_id: UUID, data: SalarioBaseUpdate, actor: CurrentUser
    ) -> SalarioBaseRead | None:
        """Actualiza un SalarioBase con validación de no-solapamiento."""
        before = await self._repo.get_by_id(obj_id)
        if before is None:
            return None
        update_data = data.model_dump(exclude_none=True)
        instancia = await self._repo.update_with_overlap_check(obj_id, update_data)
        if instancia is None:
            return None
        await record_audit(
            self.db_session,
            actor_id=actor.real_actor_id,
            tenant_id=self.tenant_id,
            accion=LiquidacionesAuditAction.SALARIO_BASE_MODIFICAR,
            detalle={
                "operacion": "UPDATE",
                "before": {
                    "monto": str(before.monto),
                    "desde": str(before.desde),
                    "hasta": str(before.hasta) if before.hasta else None,
                },
                "after": {
                    "monto": str(instancia.monto),
                    "desde": str(instancia.desde),
                    "hasta": str(instancia.hasta) if instancia.hasta else None,
                },
            },
            filas_afectadas=1,
        )
        return SalarioBaseRead.model_validate(instancia)

    async def eliminar(self, obj_id: UUID, actor: CurrentUser) -> bool:
        """Soft delete de un SalarioBase."""
        instancia = await self._repo.get_by_id(obj_id)
        if instancia is None:
            return False
        eliminado = await self._repo.delete(obj_id)
        if eliminado:
            await record_audit(
                self.db_session,
                actor_id=actor.real_actor_id,
                tenant_id=self.tenant_id,
                accion=LiquidacionesAuditAction.SALARIO_BASE_ELIMINAR,
                detalle={"operacion": "SOFT_DELETE", "id": str(obj_id)},
                filas_afectadas=1,
            )
        return eliminado

    async def listar(self) -> list[SalarioBaseRead]:
        """Lista todos los SalarioBase activos del tenant."""
        instancias = await self._repo.list()
        return [SalarioBaseRead.model_validate(i) for i in instancias]

    async def obtener(self, obj_id: UUID) -> SalarioBaseRead | None:
        """Obtiene un SalarioBase por ID."""
        instancia = await self._repo.get_by_id(obj_id)
        if instancia is None:
            return None
        return SalarioBaseRead.model_validate(instancia)
