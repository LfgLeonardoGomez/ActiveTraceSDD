"""Repository de SalarioBase (C-18).

Scope: tenant_id obligatorio (BaseRepository fail-closed).
Operaciones: CRUD + find_vigente + validación de no-solapamiento.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.liquidaciones.exceptions import VigenciaSolapadaError
from app.modules.liquidaciones.models.salario_base import SalarioBase
from app.repositories.base import BaseRepository


class SalarioBaseRepository(BaseRepository[SalarioBase]):
    """Repository de SalarioBase con scope de tenant y validación de overlap."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, SalarioBase, tenant_id)

    async def find_vigente(self, rol: str, periodo: str) -> SalarioBase | None:
        """Busca el SalarioBase vigente para (rol, periodo).

        periodo debe ser formato AAAA-MM. Devuelve la fila cuyo rango [desde, hasta]
        contiene el primer y último día del período.
        """
        # Convertir 'AAAA-MM' a primer día del mes
        year, month = int(periodo[:4]), int(periodo[5:7])
        primer_dia = date(year, month, 1)

        query = (
            select(SalarioBase)
            .where(
                SalarioBase.tenant_id == self.tenant_id,
                SalarioBase.deleted_at.is_(None),
                SalarioBase.rol == rol,
                SalarioBase.desde <= primer_dia,
                or_(
                    SalarioBase.hasta.is_(None),
                    SalarioBase.hasta >= primer_dia,
                ),
            )
            .order_by(SalarioBase.desde.desc())
            .limit(1)
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def check_overlap(
        self,
        rol: str,
        desde: date,
        hasta: date | None,
        exclude_id: UUID | None = None,
    ) -> SalarioBase | None:
        """Verifica si existe solapamiento de vigencia para (tenant, rol).

        Retorna la fila solapada, o None si no hay solapamiento.
        """
        query = select(SalarioBase).where(
            SalarioBase.tenant_id == self.tenant_id,
            SalarioBase.deleted_at.is_(None),
            SalarioBase.rol == rol,
            # Overlap: [desde, hasta] && [b.desde, b.hasta]
            # A[a1, a2] solapa B[b1, b2] si a1 <= b2 AND a2 >= b1
            SalarioBase.desde
            <= (func.coalesce(func.cast(hasta, SalarioBase.desde.type), date(9999, 12, 31))),
            func.coalesce(
                SalarioBase.hasta, func.cast(date(9999, 12, 31), SalarioBase.hasta.type)
            )
            >= desde,
        )
        if exclude_id is not None:
            query = query.where(SalarioBase.id != exclude_id)
        result = await self.db_session.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def create_with_overlap_check(self, rol: str, monto, desde: date, hasta: date | None) -> SalarioBase:
        """Crea un SalarioBase validando no-solapamiento."""
        solapado = await self.check_overlap(rol, desde, hasta)
        if solapado:
            raise VigenciaSolapadaError("salarios_base", solapado.id)
        return await self.create(rol=rol, monto=monto, desde=desde, hasta=hasta)

    async def update_with_overlap_check(self, obj_id: UUID, data: dict) -> SalarioBase | None:
        """Actualiza un SalarioBase validando no-solapamiento."""
        instance = await self.get_by_id(obj_id)
        if instance is None:
            return None
        # Usar valores actuales si no se proveen en data
        rol = data.get("rol", instance.rol)
        desde = data.get("desde", instance.desde)
        hasta = data.get("hasta", instance.hasta)
        solapado = await self.check_overlap(rol, desde, hasta, exclude_id=obj_id)
        if solapado:
            raise VigenciaSolapadaError("salarios_base", solapado.id)
        return await self.update(obj_id, data)
