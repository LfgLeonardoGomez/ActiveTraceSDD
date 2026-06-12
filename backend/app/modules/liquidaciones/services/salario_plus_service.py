"""Service de SalarioPlus (C-18).

CRUD + validación de overlap por (grupo, rol) + validación tope_acumulacion + audit.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.dependencies import CurrentUser
from app.modules.liquidaciones.audit_codes import LiquidacionesAuditAction
from app.modules.liquidaciones.repositories.salario_plus_repo import SalarioPlusRepository
from app.modules.liquidaciones.schemas.salario_plus import (
    SalarioPlusCreate,
    SalarioPlusRead,
    SalarioPlusUpdate,
)


class SalarioPlusService:
    """Service de SalarioPlus con validación de overlap y auditoría."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._repo = SalarioPlusRepository(db_session, tenant_id)

    async def crear(self, data: SalarioPlusCreate, actor: CurrentUser) -> SalarioPlusRead:
        """Crea un SalarioPlus con validación de no-solapamiento."""
        instancia = await self._repo.create_with_overlap_check(
            grupo=data.grupo,
            rol=data.rol,
            monto=data.monto,
            desde=data.desde,
            hasta=data.hasta,
            descripcion=data.descripcion,
            tope_acumulacion=data.tope_acumulacion,
        )
        await record_audit(
            self.db_session,
            actor_id=actor.real_actor_id,
            tenant_id=self.tenant_id,
            accion=LiquidacionesAuditAction.SALARIO_PLUS_CREAR,
            detalle={
                "operacion": "CREATE",
                "after": {
                    "id": str(instancia.id),
                    "grupo": instancia.grupo,
                    "rol": instancia.rol,
                    "monto": str(instancia.monto),
                    "tope_acumulacion": str(instancia.tope_acumulacion) if instancia.tope_acumulacion else None,
                    "desde": str(instancia.desde),
                    "hasta": str(instancia.hasta) if instancia.hasta else None,
                },
            },
            filas_afectadas=1,
        )
        return SalarioPlusRead.model_validate(instancia)

    async def actualizar(
        self, obj_id: UUID, data: SalarioPlusUpdate, actor: CurrentUser
    ) -> SalarioPlusRead | None:
        """Actualiza un SalarioPlus con validación de no-solapamiento."""
        before = await self._repo.get_by_id(obj_id)
        if before is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        instancia = await self._repo.update_with_overlap_check(obj_id, update_data)
        if instancia is None:
            return None
        await record_audit(
            self.db_session,
            actor_id=actor.real_actor_id,
            tenant_id=self.tenant_id,
            accion=LiquidacionesAuditAction.SALARIO_PLUS_MODIFICAR,
            detalle={
                "operacion": "UPDATE",
                "before": {
                    "monto": str(before.monto),
                    "tope_acumulacion": str(before.tope_acumulacion) if before.tope_acumulacion else None,
                    "desde": str(before.desde),
                    "hasta": str(before.hasta) if before.hasta else None,
                },
                "after": {
                    "monto": str(instancia.monto),
                    "tope_acumulacion": str(instancia.tope_acumulacion) if instancia.tope_acumulacion else None,
                    "desde": str(instancia.desde),
                    "hasta": str(instancia.hasta) if instancia.hasta else None,
                },
            },
            filas_afectadas=1,
        )
        return SalarioPlusRead.model_validate(instancia)

    async def eliminar(self, obj_id: UUID, actor: CurrentUser) -> bool:
        """Soft delete de un SalarioPlus."""
        instancia = await self._repo.get_by_id(obj_id)
        if instancia is None:
            return False
        eliminado = await self._repo.delete(obj_id)
        if eliminado:
            await record_audit(
                self.db_session,
                actor_id=actor.real_actor_id,
                tenant_id=self.tenant_id,
                accion=LiquidacionesAuditAction.SALARIO_PLUS_ELIMINAR,
                detalle={"operacion": "SOFT_DELETE", "id": str(obj_id)},
                filas_afectadas=1,
            )
        return eliminado

    async def listar(self) -> list[SalarioPlusRead]:
        """Lista todos los SalarioPlus activos del tenant."""
        instancias = await self._repo.list()
        return [SalarioPlusRead.model_validate(i) for i in instancias]

    async def obtener(self, obj_id: UUID) -> SalarioPlusRead | None:
        """Obtiene un SalarioPlus por ID."""
        instancia = await self._repo.get_by_id(obj_id)
        if instancia is None:
            return None
        return SalarioPlusRead.model_validate(instancia)
