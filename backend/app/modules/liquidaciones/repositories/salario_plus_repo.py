"""Repository de SalarioPlus (C-18).

Scope: tenant_id obligatorio.
Operaciones: CRUD + find_vigentes_por_grupos + validación de overlap por (grupo, rol).
"""

from datetime import date
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.liquidaciones.exceptions import VigenciaSolapadaError
from app.modules.liquidaciones.models.salario_plus import SalarioPlus
from app.repositories.base import BaseRepository


class SalarioPlusRepository(BaseRepository[SalarioPlus]):
    """Repository de SalarioPlus con scope de tenant y validación de overlap."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, SalarioPlus, tenant_id)

    async def find_vigentes_por_grupos(
        self,
        grupos: list[str],
        rol: str,
        periodo: str,
    ) -> list[SalarioPlus]:
        """Busca SalarioPlus vigentes para una lista de grupos, un rol y un período.

        Retorna una fila por cada grupo que tenga vigencia en el período.
        """
        if not grupos:
            return []
        year, month = int(periodo[:4]), int(periodo[5:7])
        primer_dia = date(year, month, 1)

        query = select(SalarioPlus).where(
            SalarioPlus.tenant_id == self.tenant_id,
            SalarioPlus.deleted_at.is_(None),
            SalarioPlus.rol == rol,
            SalarioPlus.grupo.in_(grupos),
            SalarioPlus.desde <= primer_dia,
            or_(
                SalarioPlus.hasta.is_(None),
                SalarioPlus.hasta >= primer_dia,
            ),
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def find_vigente(self, grupo: str, rol: str, periodo: str) -> SalarioPlus | None:
        """Busca el SalarioPlus vigente para (grupo, rol, periodo)."""
        vigentes = await self.find_vigentes_por_grupos([grupo], rol, periodo)
        return vigentes[0] if vigentes else None

    async def check_overlap(
        self,
        grupo: str,
        rol: str,
        desde: date,
        hasta: date | None,
        exclude_id: UUID | None = None,
    ) -> SalarioPlus | None:
        """Verifica solapamiento de vigencia para (tenant, grupo, rol)."""
        query = select(SalarioPlus).where(
            SalarioPlus.tenant_id == self.tenant_id,
            SalarioPlus.deleted_at.is_(None),
            SalarioPlus.grupo == grupo,
            SalarioPlus.rol == rol,
            SalarioPlus.desde
            <= (func.coalesce(func.cast(hasta, SalarioPlus.desde.type), date(9999, 12, 31))),
            func.coalesce(
                SalarioPlus.hasta, func.cast(date(9999, 12, 31), SalarioPlus.hasta.type)
            )
            >= desde,
        )
        if exclude_id is not None:
            query = query.where(SalarioPlus.id != exclude_id)
        result = await self.db_session.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def create_with_overlap_check(
        self,
        grupo: str,
        rol: str,
        monto,
        desde: date,
        hasta: date | None,
        descripcion: str | None = None,
        tope_acumulacion=None,
    ) -> SalarioPlus:
        """Crea un SalarioPlus validando no-solapamiento."""
        solapado = await self.check_overlap(grupo, rol, desde, hasta)
        if solapado:
            raise VigenciaSolapadaError("salarios_plus", solapado.id)
        return await self.create(
            grupo=grupo,
            rol=rol,
            monto=monto,
            desde=desde,
            hasta=hasta,
            descripcion=descripcion,
            tope_acumulacion=tope_acumulacion,
        )

    async def update_with_overlap_check(self, obj_id: UUID, data: dict) -> SalarioPlus | None:
        """Actualiza un SalarioPlus validando no-solapamiento."""
        instance = await self.get_by_id(obj_id)
        if instance is None:
            return None
        grupo = data.get("grupo", instance.grupo)
        rol = data.get("rol", instance.rol)
        desde = data.get("desde", instance.desde)
        hasta = data.get("hasta", instance.hasta)
        solapado = await self.check_overlap(grupo, rol, desde, hasta, exclude_id=obj_id)
        if solapado:
            raise VigenciaSolapadaError("salarios_plus", solapado.id)
        return await self.update(obj_id, data)
