"""Helper de auditoría: AuditAction enum y función record_audit.

Llamar exclusivamente desde la capa Service, nunca desde Routers.
"""

from enum import StrEnum
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditAction(StrEnum):
    """Catálogo de códigos de acción para el log de auditoría."""

    CALIFICACIONES_IMPORTAR = "CALIFICACIONES_IMPORTAR"
    PADRON_CARGAR = "PADRON_CARGAR"
    PADRON_VACIAR = "PADRON_VACIAR"
    COMUNICACION_ENVIAR = "COMUNICACION_ENVIAR"
    COMUNICACION_APROBAR = "COMUNICACION_APROBAR"
    ASIGNACION_MODIFICAR = "ASIGNACION_MODIFICAR"
    LIQUIDACION_CERRAR = "LIQUIDACION_CERRAR"
    IMPERSONACION_INICIAR = "IMPERSONACION_INICIAR"
    IMPERSONACION_FINALIZAR = "IMPERSONACION_FINALIZAR"


async def record_audit(
    session: AsyncSession,
    actor_id: UUID,
    tenant_id: UUID,
    accion: AuditAction,
    *,
    impersonado_id: UUID | None = None,
    materia_id: UUID | None = None,
    detalle: dict | None = None,
    filas_afectadas: int = 0,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Registra una acción significativa en el log de auditoría.

    Inserta en la sesión activa (flush sin commit) para participar
    de la transacción del caller. El campo fecha_hora se auto-asigna
    por defecto del modelo (UTC).
    """
    entry = AuditLog(
        actor_id=actor_id,
        tenant_id=tenant_id,
        accion=str(accion),
        impersonado_id=impersonado_id,
        materia_id=materia_id,
        detalle=detalle,
        filas_afectadas=filas_afectadas,
        ip=ip,
        user_agent=user_agent,
    )
    session.add(entry)
    await session.commit()
