"""Seeds de permisos y audit codes del módulo liquidaciones (C-18, tasks 9.1–9.3).

seed_liquidaciones_permissions(): registra permisos liquidaciones:* y facturas:*.
seed_liquidaciones_audit_codes(): registra los códigos de auditoría.

Ambos seeds son idempotentes (no crean duplicados).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.liquidaciones.audit_codes import LiquidacionesAuditAction
from app.modules.liquidaciones.permissions import (
    LIQUIDACIONES_PERMISSIONS,
    LIQUIDACIONES_ROLE_ASSIGNMENTS,
)


async def seed_liquidaciones_permissions(db: AsyncSession) -> None:
    """Registra los permisos liquidaciones:* y facturas:* idempotentemente.

    Usa la infraestructura de RBAC de C-04 (modelos Permiso y RolPermiso).
    """
    from app.models.role import Permiso, Rol, RolPermiso  # noqa: PLC0415

    for perm_data in LIQUIDACIONES_PERMISSIONS:
        # Verificar si ya existe
        result = await db.execute(
            select(Permiso).where(Permiso.codigo == perm_data["codigo"])
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            perm = Permiso(
                codigo=perm_data["codigo"],
                nombre=perm_data["nombre"],
                modulo=perm_data["modulo"],
                descripcion=perm_data.get("descripcion"),
            )
            db.add(perm)

    await db.commit()

    # Asignar permisos a roles
    for perm_codigo, rol_codigo, es_propio in LIQUIDACIONES_ROLE_ASSIGNMENTS:
        # Buscar permiso y rol
        perm_result = await db.execute(
            select(Permiso).where(Permiso.codigo == perm_codigo)
        )
        perm = perm_result.scalar_one_or_none()

        rol_result = await db.execute(select(Rol).where(Rol.codigo == rol_codigo))
        rol = rol_result.scalar_one_or_none()

        if perm is None or rol is None:
            continue

        # Verificar si ya está asignado
        rp_result = await db.execute(
            select(RolPermiso).where(
                RolPermiso.rol_id == rol.id,
                RolPermiso.permiso_id == perm.id,
            )
        )
        if rp_result.scalar_one_or_none() is None:
            rp = RolPermiso(rol_id=rol.id, permiso_id=perm.id, es_propio=es_propio)
            db.add(rp)

    await db.commit()


async def seed_liquidaciones_audit_codes(db: AsyncSession) -> None:
    """Registra los códigos de auditoría del módulo liquidaciones idempotentemente.

    Los registra en el enum AuditAction extendido del módulo.
    En este proyecto los audit codes son StrEnum — no requieren persistencia en DB.
    Esta función es un punto de extensión para cuando se implemente
    un catálogo dinámico de audit codes (C-05+).
    """
    # Los códigos ya están definidos en LiquidacionesAuditAction (StrEnum).
    # Si C-05 expone una API de registro de códigos, se invocaría acá.
    # Por ahora es un no-op idempotente documentado.
    pass


async def run_all_seeds(db: AsyncSession) -> None:
    """Ejecuta todos los seeds del módulo en orden."""
    await seed_liquidaciones_permissions(db)
    await seed_liquidaciones_audit_codes(db)
