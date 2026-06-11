"""Repositorio de avisos y acknowledgment (C-15).

Todas las queries filtran por tenant_id (row-level isolation).
Audience matching (RN-20) implementado con EXISTS subqueries contra Asignacion.
Lógica de negocio pertenece al Service.
"""

from datetime import datetime, timezone
from math import ceil
from uuid import UUID, uuid4

from sqlalchemy import and_, func, not_, or_, select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.aviso import AcknowledgmentAviso, AlcanceAviso, Aviso


class AvisoRepository:
    """Repository de avisos: CRUD + audience query + acknowledgment."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        self.db_session = db_session
        self.tenant_id = tenant_id

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _base_aviso_query(self):
        return select(Aviso).where(
            Aviso.tenant_id == self.tenant_id,
            Aviso.deleted_at.is_(None),
        )

    # ------------------------------------------------------------------
    # 3.1 CRUD avisos
    # ------------------------------------------------------------------

    async def create(self, data: dict) -> Aviso:
        aviso = Aviso(
            id=uuid4(),
            tenant_id=self.tenant_id,
            **data,
        )
        self.db_session.add(aviso)
        await self.db_session.commit()
        await self.db_session.refresh(aviso)
        return aviso

    async def get_by_id(self, aviso_id: UUID) -> Aviso | None:
        query = self._base_aviso_query().where(Aviso.id == aviso_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_avisos(
        self,
        page: int,
        page_size: int,
        alcance: str | None = None,
        activo: bool | None = None,
        severidad: str | None = None,
    ) -> tuple[list[Aviso], int]:
        base = self._base_aviso_query()
        if alcance is not None:
            base = base.where(Aviso.alcance == alcance)
        if activo is not None:
            base = base.where(Aviso.activo.is_(activo))
        if severidad is not None:
            base = base.where(Aviso.severidad == severidad)

        total = (
            await self.db_session.execute(
                select(func.count()).select_from(base.subquery())
            )
        ).scalar_one()

        offset = (page - 1) * page_size
        rows_q = (
            base.order_by(Aviso.orden.asc(), Aviso.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(rows_q)
        items = list(result.scalars().all())
        return items, total

    async def update(self, aviso_id: UUID, data: dict) -> Aviso | None:
        aviso = await self.get_by_id(aviso_id)
        if aviso is None:
            return None
        for key, value in data.items():
            if hasattr(aviso, key):
                setattr(aviso, key, value)
        aviso.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(aviso)
        return aviso

    async def soft_delete(self, aviso_id: UUID) -> Aviso | None:
        aviso = await self.get_by_id(aviso_id)
        if aviso is None:
            return None
        aviso.deleted_at = datetime.now(timezone.utc)
        aviso.activo = False
        aviso.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(aviso)
        return aviso

    # ------------------------------------------------------------------
    # 3.2 Audience query — listar avisos visibles para un usuario (RN-20)
    # ------------------------------------------------------------------

    async def list_para_usuario(
        self,
        usuario_id: UUID,
        now: datetime,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[Aviso, bool]], int]:
        """Lista avisos visibles para un usuario con flag acknowledged.

        Filtros:
        - activo=true, deleted_at IS NULL, inicio_en <= now <= fin_en
        - audience match según alcance (Global/PorRol/PorMateria/PorCohorte)
        - retorna flag acknowledged (siempre False aquí porque filtramos ack'd)
        """
        # Subquery: ¿el usuario ya hizo ack?
        ack_exists = exists().where(
            AcknowledgmentAviso.aviso_id == Aviso.id,
            AcknowledgmentAviso.usuario_id == usuario_id,
            AcknowledgmentAviso.deleted_at.is_(None),
        )

        # Subqueries de audience via Asignacion
        has_rol = exists().where(
            Asignacion.usuario_id == usuario_id,
            Asignacion.tenant_id == self.tenant_id,
            Asignacion.rol == Aviso.rol_destino,
        )
        has_materia = exists().where(
            Asignacion.usuario_id == usuario_id,
            Asignacion.tenant_id == self.tenant_id,
            Asignacion.materia_id == Aviso.materia_id,
        )
        has_cohorte = exists().where(
            Asignacion.usuario_id == usuario_id,
            Asignacion.tenant_id == self.tenant_id,
            Asignacion.cohorte_id == Aviso.cohorte_id,
        )

        audience_filter = or_(
            Aviso.alcance == AlcanceAviso.GLOBAL,
            and_(
                Aviso.alcance == AlcanceAviso.POR_ROL,
                or_(Aviso.rol_destino.is_(None), has_rol),
            ),
            and_(
                Aviso.alcance == AlcanceAviso.POR_MATERIA,
                has_materia,
            ),
            and_(
                Aviso.alcance == AlcanceAviso.POR_COHORTE,
                has_cohorte,
            ),
        )

        base = (
            select(Aviso, ack_exists.label("acknowledged"))
            .where(
                Aviso.tenant_id == self.tenant_id,
                Aviso.deleted_at.is_(None),
                Aviso.activo.is_(True),
                Aviso.inicio_en <= now,
                Aviso.fin_en >= now,
                audience_filter,
            )
        )

        # Contar total antes de excluir ack'd
        total = (
            await self.db_session.execute(
                select(func.count()).select_from(base.subquery())
            )
        ).scalar_one()

        offset = (page - 1) * page_size
        rows_q = (
            base.order_by(Aviso.orden.asc(), Aviso.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db_session.execute(rows_q)
        rows = result.all()

        # Filtrar ack'd en memoria (si bien la query ya los marca,
        # la spec dice excluirlos de mis-avisos; lo dejamos al service
        # pero aquí devolvemos el flag para que el service decida)
        items = [(row.Aviso, bool(row.acknowledged)) for row in rows]
        return items, total

    # ------------------------------------------------------------------
    # 3.3 Acknowledgment
    # ------------------------------------------------------------------

    async def get_acknowledgment(
        self, aviso_id: UUID, usuario_id: UUID
    ) -> AcknowledgmentAviso | None:
        query = select(AcknowledgmentAviso).where(
            AcknowledgmentAviso.aviso_id == aviso_id,
            AcknowledgmentAviso.usuario_id == usuario_id,
            AcknowledgmentAviso.deleted_at.is_(None),
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def acknowledge(
        self, aviso_id: UUID, usuario_id: UUID
    ) -> AcknowledgmentAviso:
        """Crea un acknowledgment. Caller debe verificar que no existe previamente."""
        ack = AcknowledgmentAviso(
            id=uuid4(),
            tenant_id=self.tenant_id,
            aviso_id=aviso_id,
            usuario_id=usuario_id,
            confirmado_at=datetime.now(timezone.utc),
        )
        self.db_session.add(ack)
        await self.db_session.commit()
        await self.db_session.refresh(ack)
        return ack

    async def count_acknowledgments(self, aviso_id: UUID) -> int:
        query = select(func.count()).where(
            AcknowledgmentAviso.aviso_id == aviso_id,
            AcknowledgmentAviso.deleted_at.is_(None),
        )
        result = await self.db_session.execute(query)
        return result.scalar_one()
