"""Repositorio de calificaciones (C-10).

Scope aislado por docente: todas las operaciones filtran por
(tenant_id, usuario_importador_id, materia_id) — RN-04.

recalculate_aprobado: actualiza en batch el campo `aprobado` de todas
las calificaciones del scope cuando cambia el umbral (D-01 del design).
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion
from app.repositories.base import BaseRepository


class CalificacionRepository(BaseRepository[Calificacion]):
    """Repository de Calificacion con scope multi-tenant y operaciones de batch."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, Calificacion, tenant_id)

    async def bulk_upsert(
        self,
        calificaciones: list[dict],
    ) -> int:
        """Inserta o actualiza calificaciones en batch.

        Usa ON CONFLICT DO UPDATE sobre la unique constraint uq_calificacion_scope.
        Retorna el número de filas afectadas.
        """
        if not calificaciones:
            return 0

        from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: PLC0415

        stmt = pg_insert(Calificacion).values(calificaciones)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_calificacion_scope",
            set_={
                "nota_numerica": stmt.excluded.nota_numerica,
                "nota_textual": stmt.excluded.nota_textual,
                "aprobado": stmt.excluded.aprobado,
                "origen": stmt.excluded.origen,
                "importado_at": stmt.excluded.importado_at,
                "updated_at": datetime.now(timezone.utc),
                "deleted_at": None,
            },
        )
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount

    async def get_by_scope(
        self,
        usuario_importador_id: UUID,
        materia_id: UUID,
    ) -> list[Calificacion]:
        """Retorna todas las calificaciones activas del scope (docente × materia)."""
        query = (
            select(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.usuario_importador_id == usuario_importador_id,
                Calificacion.materia_id == materia_id,
                Calificacion.deleted_at.is_(None),
            )
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def recalculate_aprobado(
        self,
        usuario_importador_id: UUID,
        materia_id: UUID,
        umbral_pct: int,
        valores_aprobatorios: list[str],
    ) -> int:
        """Recalcula `aprobado` para todas las calificaciones del scope.

        Lógica:
        - nota_numerica presente: aprobado = nota_numerica >= umbral_pct (sobre 100)
          Nota: las notas son puntos sobre la nota máxima, umbral es %. Se usa
          comparación directa pct — si nota ya está en escala 0-100, es directo.
        - solo nota_textual: aprobado = nota_textual IN valores_aprobatorios.

        Retorna el número de filas actualizadas.
        """
        calificaciones = await self.get_by_scope(usuario_importador_id, materia_id)
        if not calificaciones:
            return 0

        ahora = datetime.now(timezone.utc)
        vals_aprobatorios_lower = {v.lower() for v in valores_aprobatorios}
        count = 0

        for cal in calificaciones:
            if cal.nota_numerica is not None:
                nuevo_aprobado = cal.nota_numerica >= umbral_pct
            elif cal.nota_textual is not None:
                nuevo_aprobado = cal.nota_textual.strip().lower() in vals_aprobatorios_lower
            else:
                nuevo_aprobado = False

            if cal.aprobado != nuevo_aprobado:
                cal.aprobado = nuevo_aprobado
                cal.updated_at = ahora
                count += 1

        if count:
            await self.db_session.commit()

        return count

    async def soft_delete_scope(
        self,
        usuario_importador_id: UUID,
        materia_id: UUID,
    ) -> int:
        """Soft delete de todas las calificaciones del scope (docente × materia).

        RN-04: solo afecta los datos del docente que ejecuta la operación.
        Retorna el número de filas marcadas como eliminadas.
        """
        ahora = datetime.now(timezone.utc)
        stmt = (
            update(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.usuario_importador_id == usuario_importador_id,
                Calificacion.materia_id == materia_id,
                Calificacion.deleted_at.is_(None),
            )
            .values(deleted_at=ahora, updated_at=ahora)
        )
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount

    async def get_actividades_con_nota_textual(
        self,
        usuario_importador_id: UUID,
        materia_id: UUID,
    ) -> set[tuple[UUID, str]]:
        """Retorna set de (entrada_padron_id, actividad) con nota_textual no nula.

        Usado por FinalizacionService para detectar entregas ya calificadas.
        """
        query = (
            select(Calificacion.entrada_padron_id, Calificacion.actividad)
            .where(
                Calificacion.tenant_id == self.tenant_id,
                Calificacion.usuario_importador_id == usuario_importador_id,
                Calificacion.materia_id == materia_id,
                Calificacion.nota_textual.is_not(None),
                Calificacion.deleted_at.is_(None),
            )
        )
        result = await self.db_session.execute(query)
        return {(row[0], row[1]) for row in result.all()}
