"""Repositorio de Equipo con scope de tenant y JOINs enriquecidos (C-08).

Operaciones de equipo sobre la tabla Asignacion:
- list_by_equipo / list_by_usuario: JOINs con Usuario, Materia, Carrera, Cohorte
- bulk_create_assignments: add_all + flush (atomic)
- clone_vigentes: copia asignaciones vigentes a nueva cohorte
- update_vigencia_by_equipo: batch update de fechas
- get_equipo_for_export: JOINs para exportar con/sin PII

No hereda de BaseRepository porque opera sobre JOINs y no sobre un solo modelo.
"""

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.estructura import Carrera, Cohorte, Materia
from app.models.user import Usuario


class EquipoRepository:
    """Repositorio de equipos docentes con JOINs enriquecidos."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        if tenant_id is None:
            raise ValueError("tenant_id is required")
        self.db_session = db_session
        self.tenant_id = tenant_id

    def _base_join_query(self):
        """Construye el query base con JOINs a Usuario, Materia, Carrera, Cohorte.

        Siempre filtra por tenant_id y deleted_at IS NULL en todas las tablas.
        """
        return (
            select(
                Asignacion,
                Materia.nombre.label("materia_nombre"),
                Carrera.nombre.label("carrera_nombre"),
                Cohorte.nombre.label("cohorte_nombre"),
                Usuario.nombre.label("usuario_nombre"),
                Usuario.apellidos.label("usuario_apellidos"),
            )
            .join(Usuario, Asignacion.usuario_id == Usuario.id)
            .join(Materia, Asignacion.materia_id == Materia.id, isouter=True)
            .join(Carrera, Asignacion.carrera_id == Carrera.id, isouter=True)
            .join(Cohorte, Asignacion.cohorte_id == Cohorte.id, isouter=True)
            .where(Asignacion.tenant_id == self.tenant_id)
            .where(Asignacion.deleted_at.is_(None))
            .where(Usuario.deleted_at.is_(None))
            .where(
                (Materia.deleted_at.is_(None)) | (Asignacion.materia_id.is_(None))
            )
            .where(
                (Carrera.deleted_at.is_(None)) | (Asignacion.carrera_id.is_(None))
            )
            .where(
                (Cohorte.deleted_at.is_(None)) | (Asignacion.cohorte_id.is_(None))
            )
        )

    def _apply_estado_vigencia_filter(self, query, estado_vigencia: str | None):
        """Aplica filtro de estado_vigencia calculado en DB."""
        if estado_vigencia is None:
            return query
        today = date.today()
        if estado_vigencia == "Vigente":
            query = query.where(
                (Asignacion.desde <= today)
                & ((Asignacion.hasta.is_(None)) | (Asignacion.hasta >= today))
            )
        elif estado_vigencia == "Vencida":
            query = query.where(
                (Asignacion.desde > today)
                | ((Asignacion.hasta.is_not(None)) & (Asignacion.hasta < today))
            )
        return query

    async def list_by_equipo(
        self,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_id: UUID,
        estado_vigencia: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[Any, ...]], int]:
        """Lista asignaciones de un equipo con nombres enriquecidos.

        Returns:
            Tuple (lista de tuplas (Asignacion, ...nombres), total_count).
        """
        base = (
            self._base_join_query()
            .where(Asignacion.materia_id == materia_id)
            .where(Asignacion.carrera_id == carrera_id)
            .where(Asignacion.cohorte_id == cohorte_id)
        )
        base = self._apply_estado_vigencia_filter(base, estado_vigencia)

        count_query = select(func.count()).select_from(base.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = base.limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.all())

        return items, total

    async def list_by_usuario(
        self,
        usuario_id: UUID,
        estado_vigencia: str | None = None,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[Any, ...]], int]:
        """Lista asignaciones de un usuario con nombres enriquecidos.

        Returns:
            Tuple (lista de tuplas (Asignacion, ...nombres), total_count).
        """
        base = self._base_join_query().where(Asignacion.usuario_id == usuario_id)

        if materia_id is not None:
            base = base.where(Asignacion.materia_id == materia_id)
        if carrera_id is not None:
            base = base.where(Asignacion.carrera_id == carrera_id)
        if cohorte_id is not None:
            base = base.where(Asignacion.cohorte_id == cohorte_id)

        base = self._apply_estado_vigencia_filter(base, estado_vigencia)

        count_query = select(func.count()).select_from(base.subquery())
        count_result = await self.db_session.execute(count_query)
        total = count_result.scalar_one()

        items_query = base.limit(limit).offset(offset)
        items_result = await self.db_session.execute(items_query)
        items = list(items_result.all())

        return items, total

    async def bulk_create_assignments(
        self, items: list[dict[str, Any]]
    ) -> list[Asignacion]:
        """Crea múltiples asignaciones en batch (add_all + flush).

        No hace commit — el caller debe commitear la transacción.

        Returns:
            Lista de instancias creadas (sin IDs hasta flush).
        """
        instances = []
        for item in items:
            if "tenant_id" in item:
                raise ValueError("tenant_id must not be passed explicitly")
            item["tenant_id"] = self.tenant_id
            instance = Asignacion(**item)
            instances.append(instance)

        self.db_session.add_all(instances)
        await self.db_session.flush()
        return instances

    async def clone_vigentes(
        self,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_id_origen: UUID,
        cohorte_id_destino: UUID,
        desde: date,
        hasta: date | None,
    ) -> list[Asignacion]:
        """Clona asignaciones vigentes de un equipo origen a destino.

        Returns:
            Lista de nuevas instancias creadas.
        """
        today = date.today()
        query = (
            select(Asignacion)
            .where(Asignacion.tenant_id == self.tenant_id)
            .where(Asignacion.deleted_at.is_(None))
            .where(Asignacion.materia_id == materia_id)
            .where(Asignacion.carrera_id == carrera_id)
            .where(Asignacion.cohorte_id == cohorte_id_origen)
            .where(Asignacion.desde <= today)
            .where(
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= today)
            )
        )
        result = await self.db_session.execute(query)
        originales = list(result.scalars().all())

        if not originales:
            return []

        nuevas = []
        for original in originales:
            nueva = Asignacion(
                tenant_id=self.tenant_id,
                usuario_id=original.usuario_id,
                rol=original.rol,
                desde=desde,
                hasta=hasta,
                materia_id=original.materia_id,
                carrera_id=original.carrera_id,
                cohorte_id=cohorte_id_destino,
                comisiones=original.comisiones,
                responsable_id=original.responsable_id,
            )
            nuevas.append(nueva)

        self.db_session.add_all(nuevas)
        await self.db_session.flush()
        return nuevas

    async def update_vigencia_by_equipo(
        self,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_id: UUID,
        desde: date,
        hasta: date | None,
    ) -> int:
        """Actualiza fechas de vigencia de todas las asignaciones vigentes del equipo.

        Returns:
            Cantidad de filas actualizadas.
        """
        today = date.today()
        query = (
            select(Asignacion)
            .where(Asignacion.tenant_id == self.tenant_id)
            .where(Asignacion.deleted_at.is_(None))
            .where(Asignacion.materia_id == materia_id)
            .where(Asignacion.carrera_id == carrera_id)
            .where(Asignacion.cohorte_id == cohorte_id)
            .where(Asignacion.desde <= today)
            .where(
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= today)
            )
        )
        result = await self.db_session.execute(query)
        asignaciones = list(result.scalars().all())

        if not asignaciones:
            return 0

        for asig in asignaciones:
            asig.desde = desde
            asig.hasta = hasta

        await self.db_session.flush()
        return len(asignaciones)

    async def get_equipo_for_export(
        self,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_id: UUID,
        include_pii: bool,
    ) -> list[tuple[Any, ...]]:
        """Obtiene asignaciones del equipo para exportar.

        Si include_pii=False, excluye email, dni, cbu (no se incluyen en el query).
        """
        columns = [
            Asignacion,
            Materia.nombre.label("materia_nombre"),
            Carrera.nombre.label("carrera_nombre"),
            Cohorte.nombre.label("cohorte_nombre"),
            Usuario.nombre.label("usuario_nombre"),
            Usuario.apellidos.label("usuario_apellidos"),
        ]
        if include_pii:
            # El repositorio de Usuario descifra PII transparentemente al leer,
            # pero aquí hacemos un query directo. Solo incluimos los campos raw.
            columns.extend([
                Usuario.email.label("usuario_email"),
                Usuario.dni.label("usuario_dni"),
                Usuario.cbu.label("usuario_cbu"),
            ])

        query = (
            select(*columns)
            .join(Usuario, Asignacion.usuario_id == Usuario.id)
            .join(Materia, Asignacion.materia_id == Materia.id, isouter=True)
            .join(Carrera, Asignacion.carrera_id == Carrera.id, isouter=True)
            .join(Cohorte, Asignacion.cohorte_id == Cohorte.id, isouter=True)
            .where(Asignacion.tenant_id == self.tenant_id)
            .where(Asignacion.deleted_at.is_(None))
            .where(Asignacion.materia_id == materia_id)
            .where(Asignacion.carrera_id == carrera_id)
            .where(Asignacion.cohorte_id == cohorte_id)
            .where(Usuario.deleted_at.is_(None))
            .where(
                (Materia.deleted_at.is_(None)) | (Asignacion.materia_id.is_(None))
            )
            .where(
                (Carrera.deleted_at.is_(None)) | (Asignacion.carrera_id.is_(None))
            )
            .where(
                (Cohorte.deleted_at.is_(None)) | (Asignacion.cohorte_id.is_(None))
            )
        )

        result = await self.db_session.execute(query)
        return list(result.all())
