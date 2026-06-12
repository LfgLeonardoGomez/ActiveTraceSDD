"""Service de MateriaGrupoPlus (C-18, PA-22).

CRUD + validación de overlap + audit MATERIA_GRUPO_PLUS_MODIFICAR.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.dependencies import CurrentUser
from app.modules.liquidaciones.audit_codes import LiquidacionesAuditAction
from app.modules.liquidaciones.repositories.materia_grupo_plus_repo import (
    MateriaGrupoPlusRepository,
)
from app.modules.liquidaciones.schemas.materia_grupo_plus import (
    MateriaGrupoPlusCreate,
    MateriaGrupoPlusRead,
    MateriaGrupoPlusUpdate,
)


class MateriaGrupoPlusService:
    """Service de MateriaGrupoPlus con validación de overlap y auditoría."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._repo = MateriaGrupoPlusRepository(db_session, tenant_id)

    async def crear(self, data: MateriaGrupoPlusCreate, actor: CurrentUser) -> MateriaGrupoPlusRead:
        """Crea un MateriaGrupoPlus con validación de no-solapamiento."""
        instancia = await self._repo.create_with_overlap_check(
            materia_id=data.materia_id,
            grupo=data.grupo,
            desde=data.desde,
            hasta=data.hasta,
        )
        await record_audit(
            self.db_session,
            actor_id=actor.real_actor_id,
            tenant_id=self.tenant_id,
            accion=LiquidacionesAuditAction.MATERIA_GRUPO_PLUS_CREAR,
            detalle={
                "operacion": "CREATE",
                "after": {
                    "id": str(instancia.id),
                    "materia_id": str(instancia.materia_id),
                    "grupo": instancia.grupo,
                    "desde": str(instancia.desde),
                    "hasta": str(instancia.hasta) if instancia.hasta else None,
                },
            },
            filas_afectadas=1,
        )
        return MateriaGrupoPlusRead.model_validate(instancia)

    async def actualizar(
        self, obj_id: UUID, data: MateriaGrupoPlusUpdate, actor: CurrentUser
    ) -> MateriaGrupoPlusRead | None:
        """Actualiza un MateriaGrupoPlus con validación de no-solapamiento."""
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
            accion=LiquidacionesAuditAction.MATERIA_GRUPO_PLUS_MODIFICAR,
            detalle={
                "operacion": "UPDATE",
                "before": {
                    "grupo": before.grupo,
                    "desde": str(before.desde),
                    "hasta": str(before.hasta) if before.hasta else None,
                },
                "after": {
                    "grupo": instancia.grupo,
                    "desde": str(instancia.desde),
                    "hasta": str(instancia.hasta) if instancia.hasta else None,
                },
            },
            filas_afectadas=1,
        )
        return MateriaGrupoPlusRead.model_validate(instancia)

    async def eliminar(self, obj_id: UUID, actor: CurrentUser) -> bool:
        """Soft delete de un MateriaGrupoPlus."""
        instancia = await self._repo.get_by_id(obj_id)
        if instancia is None:
            return False
        eliminado = await self._repo.delete(obj_id)
        if eliminado:
            await record_audit(
                self.db_session,
                actor_id=actor.real_actor_id,
                tenant_id=self.tenant_id,
                accion=LiquidacionesAuditAction.MATERIA_GRUPO_PLUS_ELIMINAR,
                detalle={"operacion": "SOFT_DELETE", "id": str(obj_id)},
                filas_afectadas=1,
            )
        return eliminado

    async def listar(self) -> list[MateriaGrupoPlusRead]:
        """Lista todos los MateriaGrupoPlus activos del tenant."""
        instancias = await self._repo.list()
        return [MateriaGrupoPlusRead.model_validate(i) for i in instancias]

    async def obtener(self, obj_id: UUID) -> MateriaGrupoPlusRead | None:
        """Obtiene un MateriaGrupoPlus por ID."""
        instancia = await self._repo.get_by_id(obj_id)
        if instancia is None:
            return None
        return MateriaGrupoPlusRead.model_validate(instancia)
