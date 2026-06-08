"""Tests TDD — AuditLogRepository (C-05).

Verifica:
- insert registra un AuditLog en la sesión
- list_by_tenant retorna solo registros del tenant correcto
- aislamiento: registros de otro tenant no aparecen
"""

import pytest
from uuid import uuid4

from app.models.audit_log import AuditLog
from app.models.user import Usuario
from app.repositories.audit_log_repository import AuditLogRepository


def _make_user(tenant_id) -> Usuario:
    return Usuario(
        tenant_id=tenant_id,
        nombre="Test",
        apellidos="User",
        email=f"user_{uuid4().hex[:8]}@test.com",
        estado="Activo",
    )


def _make_entry(tenant_id, actor_id, accion: str = "TEST_ACTION") -> AuditLog:
    return AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        accion=accion,
    )


class TestAuditLogRepository:
    """Tests para AuditLogRepository."""

    @pytest.mark.asyncio
    async def test_insert_creates_record(self, db_session, default_tenant) -> None:
        """RED: insert persiste un AuditLog en la sesión."""
        user = _make_user(default_tenant.id)
        db_session.add(user)
        await db_session.flush()

        repo = AuditLogRepository(db_session, default_tenant.id)
        entry = _make_entry(default_tenant.id, user.id, "PADRON_CARGAR")
        await repo.insert(entry)

        records = await repo.list_by_tenant()
        assert len(records) == 1
        assert records[0].accion == "PADRON_CARGAR"
        assert records[0].actor_id == user.id
        assert records[0].tenant_id == default_tenant.id

    @pytest.mark.asyncio
    async def test_list_by_tenant_scoped(self, db_session, default_tenant) -> None:
        """GREEN: list_by_tenant solo retorna registros del tenant correcto."""
        user = _make_user(default_tenant.id)
        db_session.add(user)
        await db_session.flush()

        repo = AuditLogRepository(db_session, default_tenant.id)
        for i in range(3):
            await repo.insert(_make_entry(default_tenant.id, user.id, f"ACTION_{i}"))

        records = await repo.list_by_tenant()
        assert len(records) == 3
        assert all(r.tenant_id == default_tenant.id for r in records)

    @pytest.mark.asyncio
    async def test_list_by_tenant_does_not_cross_tenants(self, db_session, default_tenant) -> None:
        """TRIANGULATE: registros de otro tenant no aparecen."""
        # Tenant A
        user_a = _make_user(default_tenant.id)
        db_session.add(user_a)
        await db_session.flush()

        repo_a = AuditLogRepository(db_session, default_tenant.id)
        await repo_a.insert(_make_entry(default_tenant.id, user_a.id, "ACTION_TENANT_A"))

        # Tenant B (diferente)
        from app.models.tenant import Tenant
        tenant_b = Tenant(nombre="Tenant B", slug="tenant-b", activo=True)
        db_session.add(tenant_b)
        await db_session.flush()

        user_b = _make_user(tenant_b.id)
        db_session.add(user_b)
        await db_session.flush()

        repo_b = AuditLogRepository(db_session, tenant_b.id)
        await repo_b.insert(_make_entry(tenant_b.id, user_b.id, "ACTION_TENANT_B"))

        # Cada repo solo ve sus propios registros
        records_a = await repo_a.list_by_tenant()
        records_b = await repo_b.list_by_tenant()

        assert len(records_a) == 1
        assert records_a[0].accion == "ACTION_TENANT_A"

        assert len(records_b) == 1
        assert records_b[0].accion == "ACTION_TENANT_B"

    @pytest.mark.asyncio
    async def test_repository_requires_tenant_id(self, db_session) -> None:
        """TRIANGULATE: instanciar sin tenant_id lanza ValueError."""
        with pytest.raises(ValueError, match="tenant_id is required"):
            AuditLogRepository(db_session, None)

    @pytest.mark.asyncio
    async def test_insert_nullable_fields_accepted(self, db_session, default_tenant) -> None:
        """TRIANGULATE: campos opcionales nulos se aceptan sin error."""
        user = _make_user(default_tenant.id)
        db_session.add(user)
        await db_session.flush()

        entry = AuditLog(
            tenant_id=default_tenant.id,
            actor_id=user.id,
            accion="COMUNICACION_ENVIAR",
            impersonado_id=None,
            materia_id=None,
            detalle=None,
            filas_afectadas=0,
            ip=None,
            user_agent=None,
        )
        repo = AuditLogRepository(db_session, default_tenant.id)
        await repo.insert(entry)

        records = await repo.list_by_tenant()
        assert len(records) == 1
        assert records[0].impersonado_id is None
        assert records[0].materia_id is None
        assert records[0].detalle is None
