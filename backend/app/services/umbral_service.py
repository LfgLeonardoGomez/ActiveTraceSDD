"""Service de umbral de aprobación por asignación (C-10).

Provee get y upsert del umbral con recálculo batch de aprobado (D-06 del design).
Cuando el docente cambia su umbral, todas sus calificaciones en esa materia
se recalculan en la misma transacción.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.repositories.asignaciones import AsignacionRepository
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.umbral_repository import UmbralRepository
from app.schemas.umbral import UmbralMateriaRead, UmbralMateriaUpsert

_DEFAULT_UMBRAL_PCT = 60
_DEFAULT_VALORES_APROBATORIOS = ["Satisfactorio", "Supera lo esperado"]


class UmbralService:
    """Service del umbral de aprobación."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._umbral_repo = UmbralRepository(db_session, tenant_id)
        self._asig_repo = AsignacionRepository(db_session, tenant_id)
        self._cal_repo = CalificacionRepository(db_session, tenant_id)

    async def _get_asignacion_id(
        self, current_user: CurrentUser, materia_id: UUID
    ) -> UUID | None:
        """Retorna la asignacion_id vigente del docente en la materia, o None."""
        asignaciones, _ = await self._asig_repo.list_paginated(
            usuario_id=current_user.id,
            materia_id=materia_id,
            incluir_vencidas=False,
            limit=1,
        )
        return asignaciones[0].id if asignaciones else None

    async def get_umbral(
        self,
        materia_id: UUID,
        current_user: CurrentUser,
    ) -> UmbralMateriaRead:
        """Devuelve el umbral configurado para la materia, o el default 60%.

        Si no existe UmbralMateria, retorna el valor por defecto con es_default=True.
        """
        asignacion_id = await self._get_asignacion_id(current_user, materia_id)

        if asignacion_id is None:
            return UmbralMateriaRead(
                umbral_pct=_DEFAULT_UMBRAL_PCT,
                valores_aprobatorios=_DEFAULT_VALORES_APROBATORIOS,
                es_default=True,
            )

        umbral = await self._umbral_repo.get_by_asignacion(asignacion_id, materia_id)

        if umbral is None:
            return UmbralMateriaRead(
                umbral_pct=_DEFAULT_UMBRAL_PCT,
                valores_aprobatorios=_DEFAULT_VALORES_APROBATORIOS,
                es_default=True,
            )

        return UmbralMateriaRead(
            id=umbral.id,
            tenant_id=umbral.tenant_id,
            asignacion_id=umbral.asignacion_id,
            materia_id=umbral.materia_id,
            umbral_pct=umbral.umbral_pct,
            valores_aprobatorios=umbral.valores_aprobatorios,
            es_default=False,
        )

    async def upsert_umbral(
        self,
        materia_id: UUID,
        data: UmbralMateriaUpsert,
        current_user: CurrentUser,
    ) -> UmbralMateriaRead:
        """Crea o actualiza el umbral y recalcula aprobado en batch (D-06).

        El recálculo ocurre en la misma transacción del upsert.
        Solo afecta las calificaciones del docente en esa materia (RN-04).
        """
        asignacion_id = await self._get_asignacion_id(current_user, materia_id)

        if asignacion_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés una asignación activa en esta materia.",
            )

        umbral = await self._umbral_repo.upsert(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=data.umbral_pct,
            valores_aprobatorios=data.valores_aprobatorios,
        )

        # Recalcular aprobado en batch para todas las calificaciones del scope (D-06)
        await self._cal_repo.recalculate_aprobado(
            usuario_importador_id=current_user.id,
            materia_id=materia_id,
            umbral_pct=data.umbral_pct,
            valores_aprobatorios=data.valores_aprobatorios,
        )

        return UmbralMateriaRead(
            id=umbral.id,
            tenant_id=umbral.tenant_id,
            asignacion_id=umbral.asignacion_id,
            materia_id=umbral.materia_id,
            umbral_pct=umbral.umbral_pct,
            valores_aprobatorios=umbral.valores_aprobatorios,
            es_default=False,
        )
