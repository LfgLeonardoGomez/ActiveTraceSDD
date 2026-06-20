"""Seed del admin inicial para desarrollo. Idempotente.

Crea admin@admin.com / admin123 con rol ADMIN en el tenant default.
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.asignacion import Asignacion
from app.models.tenant import Tenant
from app.repositories.usuarios import UsuarioRepository


async def seed_admin(db: AsyncSession) -> None:
    """Crea admin inicial si no existe. Idempotente.

    - Busca el tenant default (slug='default').
    - Verifica si ya existe admin@admin.com via email_hash (lookup
      deterministico, no compara contra email encriptado en DB).
    - Crea el usuario con password hasheado.
    - Asigna rol ADMIN sin fecha de vencimiento.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.slug == "default").limit(1)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        return

    tenant_id = tenant.id

    repo = UsuarioRepository(db, tenant_id)
    existing = await repo.get_by_email_hash("admin@admin.com")
    if existing is not None:
        return

    user = await repo.create(
        nombre="Admin",
        apellidos="Sistema",
        email="admin@admin.com",
        estado="activo",
        password_hash=hash_password("admin123"),
    )

    asignacion = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user.id,
        rol="ADMIN",
        desde=date.today(),
        hasta=None,
    )
    db.add(asignacion)
    await db.commit()
