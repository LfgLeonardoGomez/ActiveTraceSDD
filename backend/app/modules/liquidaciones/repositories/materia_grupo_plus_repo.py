"""Repository de MateriaGrupoPlus (C-18, PA-22).

Scope: tenant_id obligatorio.
Operaciones: CRUD + find_grupo_vigente + find_materias_por_grupo + overlap check.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.liquidaciones.exceptions import VigenciaSolapadaError
from app.modules.liquidaciones.models.materia_grupo_plus import MateriaGrupoPlus
from app.repositories.base import BaseRepository


class MateriaGrupoPlusRepository(BaseRepository[MateriaGrupoPlus]):
    """Repository de MateriaGrupoPlus con scope de tenant y validación de overlap."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, MateriaGrupoPlus, tenant_id)

    async def find_grupo_vigente(self, materia_id: UUID, periodo: str) -> str | None:
        """Busca el grupo de Plus vigente para (materia_id, periodo).

        Retorna el nombre del grupo, o None si la materia no tiene mapeo vigente.
        """
        year, month = int(periodo[:4]), int(periodo[5:7])
        primer_dia = date(year, month, 1)

        query = (
            select(MateriaGrupoPlus)
            .where(
                MateriaGrupoPlus.tenant_id == self.tenant_id,
                MateriaGrupoPlus.deleted_at.is_(None),
                MateriaGrupoPlus.materia_id == materia_id,
                MateriaGrupoPlus.desde <= primer_dia,
                or_(
                    MateriaGrupoPlus.hasta.is_(None),
                    MateriaGrupoPlus.hasta >= primer_dia,
                ),
            )
            .order_by(MateriaGrupoPlus.desde.desc())
            .limit(1)
        )
        result = await self.db_session.execute(query)
        row = result.scalar_one_or_none()
        return row.grupo if row is not None else None

    async def find_materias_por_grupo(self, grupo: str, periodo: str) -> list[UUID]:
        """Retorna los materia_id cuyo grupo vigente es el dado.

        Útil para reverse lookup (¿qué materias son del grupo PROG en X período?).
        """
        year, month = int(periodo[:4]), int(periodo[5:7])
        primer_dia = date(year, month, 1)

        query = select(MateriaGrupoPlus.materia_id).where(
            MateriaGrupoPlus.tenant_id == self.tenant_id,
            MateriaGrupoPlus.deleted_at.is_(None),
            MateriaGrupoPlus.grupo == grupo,
            MateriaGrupoPlus.desde <= primer_dia,
            or_(
                MateriaGrupoPlus.hasta.is_(None),
                MateriaGrupoPlus.hasta >= primer_dia,
            ),
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def check_overlap(
        self,
        materia_id: UUID,
        desde: date,
        hasta: date | None,
        exclude_id: UUID | None = None,
    ) -> MateriaGrupoPlus | None:
        """Verifica solapamiento de vigencia para (tenant, materia_id)."""
        query = select(MateriaGrupoPlus).where(
            MateriaGrupoPlus.tenant_id == self.tenant_id,
            MateriaGrupoPlus.deleted_at.is_(None),
            MateriaGrupoPlus.materia_id == materia_id,
            MateriaGrupoPlus.desde
            <= (
                func.coalesce(
                    func.cast(hasta, MateriaGrupoPlus.desde.type), date(9999, 12, 31)
                )
            ),
            func.coalesce(
                MateriaGrupoPlus.hasta,
                func.cast(date(9999, 12, 31), MateriaGrupoPlus.hasta.type),
            )
            >= desde,
        )
        if exclude_id is not None:
            query = query.where(MateriaGrupoPlus.id != exclude_id)
        result = await self.db_session.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def create_with_overlap_check(
        self,
        materia_id: UUID,
        grupo: str,
        desde: date,
        hasta: date | None,
    ) -> MateriaGrupoPlus:
        """Crea un MateriaGrupoPlus validando no-solapamiento."""
        solapado = await self.check_overlap(materia_id, desde, hasta)
        if solapado:
            raise VigenciaSolapadaError("materia_grupo_plus", solapado.id)
        return await self.create(materia_id=materia_id, grupo=grupo, desde=desde, hasta=hasta)

    async def update_with_overlap_check(self, obj_id: UUID, data: dict) -> MateriaGrupoPlus | None:
        """Actualiza un MateriaGrupoPlus validando no-solapamiento."""
        instance = await self.get_by_id(obj_id)
        if instance is None:
            return None
        materia_id = data.get("materia_id", instance.materia_id)
        desde = data.get("desde", instance.desde)
        hasta = data.get("hasta", instance.hasta)
        solapado = await self.check_overlap(materia_id, desde, hasta, exclude_id=obj_id)
        if solapado:
            raise VigenciaSolapadaError("materia_grupo_plus", solapado.id)
        return await self.update(obj_id, data)
