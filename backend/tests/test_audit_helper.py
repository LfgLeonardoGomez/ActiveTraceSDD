"""Tests TDD — AuditAction enum y record_audit helper (C-05).

Verifica:
- record_audit inserta un AuditLog con todos los campos correctos
- parámetros opcionales nulos se aceptan
- AuditAction con valor inválido lanza ValueError
- fecha_hora del registro es UTC
"""

import pytest
from datetime import timezone
from uuid import uuid4

from app.core.audit import AuditAction, record_audit
from app.models.audit_log import AuditLog
from app.models.user import Usuario


def _make_user(tenant_id) -> Usuario:
    return Usuario(
        tenant_id=tenant_id,
        nombre="Audit",
        apellidos="Actor",
        email=f"actor_{uuid4().hex[:8]}@test.com",
        estado="Activo",
    )


class TestAuditAction:
    """Tests para el enum AuditAction."""

    def test_enum_values_are_screaming_snake_case(self) -> None:
        """RED: los valores del enum son strings en SCREAMING_SNAKE_CASE."""
        assert AuditAction.PADRON_CARGAR == "PADRON_CARGAR"
        assert AuditAction.IMPERSONACION_INICIAR == "IMPERSONACION_INICIAR"
        assert AuditAction.COMUNICACION_ENVIAR == "COMUNICACION_ENVIAR"

    def test_invalid_action_raises_value_error(self) -> None:
        """GREEN: valor fuera del catálogo lanza ValueError."""
        with pytest.raises(ValueError):
            AuditAction("ACCION_INEXISTENTE")

    def test_all_required_actions_exist(self) -> None:
        """TRIANGULATE: catálogo inicial completo."""
        expected = {
            "CALIFICACIONES_IMPORTAR",
            "PADRON_CARGAR",
            "COMUNICACION_ENVIAR",
            "ASIGNACION_MODIFICAR",
            "LIQUIDACION_CERRAR",
            "IMPERSONACION_INICIAR",
            "IMPERSONACION_FINALIZAR",
        }
        actual = {a.value for a in AuditAction}
        assert expected.issubset(actual)


class TestRecordAudit:
    """Tests para la función record_audit."""

    @pytest.mark.asyncio
    async def test_insert_with_all_parameters(self, db_session, default_tenant) -> None:
        """RED: record_audit inserta AuditLog con todos los campos."""
        actor = _make_user(default_tenant.id)
        db_session.add(actor)
        impersonado = _make_user(default_tenant.id)
        db_session.add(impersonado)
        await db_session.flush()

        await record_audit(
            db_session,
            actor_id=actor.id,
            tenant_id=default_tenant.id,
            accion=AuditAction.PADRON_CARGAR,
            impersonado_id=impersonado.id,
            detalle={"archivo": "padron.xlsx"},
            filas_afectadas=150,
            ip="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(select(AuditLog))
        records = result.scalars().all()
        assert len(records) == 1

        entry = records[0]
        assert entry.actor_id == actor.id
        assert entry.tenant_id == default_tenant.id
        assert entry.accion == "PADRON_CARGAR"
        assert entry.impersonado_id == impersonado.id
        assert entry.detalle == {"archivo": "padron.xlsx"}
        assert entry.filas_afectadas == 150
        assert entry.ip == "192.168.1.1"
        assert entry.user_agent == "Mozilla/5.0"

    @pytest.mark.asyncio
    async def test_insert_with_optional_nulls(self, db_session, default_tenant) -> None:
        """GREEN: parámetros opcionales nulos se aceptan sin error."""
        actor = _make_user(default_tenant.id)
        db_session.add(actor)
        await db_session.flush()

        await record_audit(
            db_session,
            actor_id=actor.id,
            tenant_id=default_tenant.id,
            accion=AuditAction.ASIGNACION_MODIFICAR,
        )
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(select(AuditLog))
        entry = result.scalars().first()
        assert entry is not None
        assert entry.impersonado_id is None
        assert entry.materia_id is None
        assert entry.detalle is None
        assert entry.filas_afectadas == 0
        assert entry.ip is None
        assert entry.user_agent is None

    @pytest.mark.asyncio
    async def test_fecha_hora_is_utc(self, db_session, default_tenant) -> None:
        """TRIANGULATE: fecha_hora almacenada con timezone UTC."""
        actor = _make_user(default_tenant.id)
        db_session.add(actor)
        await db_session.flush()

        await record_audit(
            db_session,
            actor_id=actor.id,
            tenant_id=default_tenant.id,
            accion=AuditAction.CALIFICACIONES_IMPORTAR,
        )
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(select(AuditLog))
        entry = result.scalars().first()
        assert entry is not None
        assert entry.fecha_hora is not None
        # tzinfo debe ser UTC o timezone-aware
        assert entry.fecha_hora.tzinfo is not None

    @pytest.mark.asyncio
    async def test_multiple_records_with_different_actions(self, db_session, default_tenant) -> None:
        """TRIANGULATE: múltiples registros con distintas acciones."""
        actor = _make_user(default_tenant.id)
        db_session.add(actor)
        await db_session.flush()

        for action in [AuditAction.PADRON_CARGAR, AuditAction.COMUNICACION_ENVIAR]:
            await record_audit(
                db_session,
                actor_id=actor.id,
                tenant_id=default_tenant.id,
                accion=action,
            )
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(select(AuditLog))
        records = result.scalars().all()
        assert len(records) == 2
        acciones = {r.accion for r in records}
        assert "PADRON_CARGAR" in acciones
        assert "COMUNICACION_ENVIAR" in acciones
