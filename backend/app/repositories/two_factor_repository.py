"""Repository para TwoFactorEnrollment.

Operaciones: crear/obtener, actualizar secreto, confirmar, obtener activo,
soft-delete por usuario.
"""

from uuid import UUID

from sqlalchemy import select, update

from app.models.two_factor_enrollment import TwoFactorEnrollment
from app.repositories.base import BaseRepository


class TwoFactorRepository(BaseRepository[TwoFactorEnrollment]):
    """Repositorio de enrollments de 2FA."""

    def __init__(self, db_session, tenant_id: UUID) -> None:
        super().__init__(db_session, TwoFactorEnrollment, tenant_id)

    async def get_active_for_user(self, user_id: UUID) -> TwoFactorEnrollment | None:
        """Busca el enrollment activo (no soft-deleted) de un usuario."""
        query = (
            self._base_query()
            .where(TwoFactorEnrollment.user_id == user_id)
            .order_by(TwoFactorEnrollment.created_at.desc())
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def update_secret(
        self, user_id: UUID, encrypted_secret: str
    ) -> TwoFactorEnrollment:
        """Actualiza o crea un enrollment con un nuevo secreto cifrado."""
        enrollment = await self.get_active_for_user(user_id)
        if enrollment:
            enrollment.encrypted_secret = encrypted_secret
            enrollment.status = "pending"
            await self.db_session.commit()
            await self.db_session.refresh(enrollment)
            return enrollment
        return await self.create(
            user_id=user_id,
            encrypted_secret=encrypted_secret,
            status="pending",
        )

    async def confirm(self, user_id: UUID) -> None:
        """Marca el enrollment como confirmado."""
        stmt = (
            update(TwoFactorEnrollment)
            .where(
                TwoFactorEnrollment.user_id == user_id,
                TwoFactorEnrollment.tenant_id == self.tenant_id,
                TwoFactorEnrollment.deleted_at.is_(None),
            )
            .values(status="confirmed")
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()

    async def soft_delete_for_user(self, user_id: UUID) -> None:
        """Soft-deletea el enrollment de un usuario."""
        from datetime import datetime, timezone

        stmt = (
            update(TwoFactorEnrollment)
            .where(
                TwoFactorEnrollment.user_id == user_id,
                TwoFactorEnrollment.tenant_id == self.tenant_id,
                TwoFactorEnrollment.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()
