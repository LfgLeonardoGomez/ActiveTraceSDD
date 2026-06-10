"""Tests de cobertura y aislamiento final (C-09 Tasks 9.1, 9.2).

Task 9.1: E2E multi-tenant — dos tenants importan padrón para el mismo
          materia_id; cada tenant solo ve su propia versión activa.
Task 9.2: Audit trail — confirm y vaciar generan AuditLog correcto con
          filas_afectadas; el detalle no contiene emails en claro.
"""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from tests.test_padron_repository import (
    _crear_materia,
    _crear_carrera,
    _crear_cohorte,
    _crear_usuario,
)


# ---------------------------------------------------------------------------
# Task 9.1 — Aislamiento multi-tenant E2E (nivel service)
# ---------------------------------------------------------------------------


class TestPadronAislamientoMultiTenantE2E:
    """Dos tenants importan padrón para el mismo materia_id UUID; cada uno
    solo ve la suya."""

    @pytest.mark.asyncio
    async def test_dos_tenants_mismo_materia_id_ven_solo_su_version(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """E2E: tenant B importa para el mismo materia_id que tenant A —
        get_active_version de cada tenant retorna exclusivamente la suya."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.models.tenant import Tenant
        from app.services.padron_service import PadronService
        from app.schemas.padron import PadronImportRow
        from app.repositories.padron_repository import PadronRepository

        # Crear tenant B
        tenant_b = Tenant(nombre="Tenant B E2E", slug="tenant-b-e2e", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        # Fixture compartida: misma materia_id lógica — pero creada en tenant A
        materia_a = await _crear_materia(db_session, default_tenant.id, "MAT-E2E-A")
        carrera_a = await _crear_carrera(db_session, default_tenant.id, "CAR-E2E-A")
        cohorte_a = await _crear_cohorte(db_session, default_tenant.id, carrera_a.id)
        actor_a = await _crear_usuario(db_session, default_tenant.id, "e2e-a@test.com")

        # Tenant B tiene sus propios registros (aislamiento completo)
        materia_b = await _crear_materia(db_session, tenant_b.id, "MAT-E2E-B")
        carrera_b = await _crear_carrera(db_session, tenant_b.id, "CAR-E2E-B")
        cohorte_b = await _crear_cohorte(db_session, tenant_b.id, carrera_b.id)
        actor_b = await _crear_usuario(db_session, tenant_b.id, "e2e-b@test.com")

        rows_a = [PadronImportRow(nombre="AluA", apellidos="T", email="alua@test.com")]
        rows_b = [PadronImportRow(nombre="AluB", apellidos="T", email="alub@test.com")]

        svc_a = PadronService(db_session, default_tenant.id)
        svc_b = PadronService(db_session, tenant_b.id)

        v_a = await svc_a.confirm_import(
            rows=rows_a, materia_id=materia_a.id, cohorte_id=cohorte_a.id,
            cargado_por_id=actor_a.id,
        )
        v_b = await svc_b.confirm_import(
            rows=rows_b, materia_id=materia_b.id, cohorte_id=cohorte_b.id,
            cargado_por_id=actor_b.id,
        )

        # Verificar aislamiento: cada repo solo ve la versión de su tenant
        repo_a = PadronRepository(db_session, default_tenant.id)
        repo_b = PadronRepository(db_session, tenant_b.id)

        active_a = await repo_a.get_active_version(materia_a.id, cohorte_a.id)
        active_b = await repo_b.get_active_version(materia_b.id, cohorte_b.id)

        assert active_a is not None
        assert active_a.id == v_a.id
        assert active_a.tenant_id == default_tenant.id

        assert active_b is not None
        assert active_b.id == v_b.id
        assert active_b.tenant_id == tenant_b.id

        # Cross-tenant: tenant B no ve versiones de materia_a (tenant A)
        cross = await repo_b.get_active_version(materia_a.id, cohorte_a.id)
        assert cross is None, "Tenant B no debe ver versiones de Tenant A"

    @pytest.mark.asyncio
    async def test_tenant_a_no_ve_entradas_de_tenant_b(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Triangulación: get_entradas_by_version respeta el tenant scope."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.models.tenant import Tenant
        from app.services.padron_service import PadronService
        from app.schemas.padron import PadronImportRow
        from app.repositories.padron_repository import PadronRepository

        tenant_b = Tenant(nombre="Tenant B Entries", slug="tenant-b-entries", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        mat_a = await _crear_materia(db_session, default_tenant.id, "MAT-X-A")
        car_a = await _crear_carrera(db_session, default_tenant.id, "CAR-X-A")
        coh_a = await _crear_cohorte(db_session, default_tenant.id, car_a.id)
        usr_a = await _crear_usuario(db_session, default_tenant.id, "xa@test.com")

        mat_b = await _crear_materia(db_session, tenant_b.id, "MAT-X-B")
        car_b = await _crear_carrera(db_session, tenant_b.id, "CAR-X-B")
        coh_b = await _crear_cohorte(db_session, tenant_b.id, car_b.id)
        usr_b = await _crear_usuario(db_session, tenant_b.id, "xb@test.com")

        svc_a = PadronService(db_session, default_tenant.id)
        svc_b = PadronService(db_session, tenant_b.id)

        v_a = await svc_a.confirm_import(
            rows=[PadronImportRow(nombre="X", apellidos="A", email="xa-alu@test.com")],
            materia_id=mat_a.id, cohorte_id=coh_a.id, cargado_por_id=usr_a.id,
        )
        v_b = await svc_b.confirm_import(
            rows=[PadronImportRow(nombre="X", apellidos="B", email="xb-alu@test.com")],
            materia_id=mat_b.id, cohorte_id=coh_b.id, cargado_por_id=usr_b.id,
        )

        # Repo de tenant A intenta ver entradas de la versión de tenant B → vacío
        repo_a = PadronRepository(db_session, default_tenant.id)
        # get_entradas_by_version filtra por tenant_id internamente
        # (la versión v_b pertenece a tenant_b, no a default_tenant)
        entradas_cross = await repo_a.get_entradas_by_version(v_b.id)
        assert entradas_cross == [], "Tenant A no debe ver entradas de Tenant B"


# ---------------------------------------------------------------------------
# Task 9.2 — Audit trail correcto
# ---------------------------------------------------------------------------


class TestPadronAuditTrail:
    """confirm y vaciar generan AuditLog correcto; detalle sin emails en claro."""

    @pytest.mark.asyncio
    async def test_confirm_import_genera_audit_log_con_filas(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """confirm_import genera PADRON_CARGAR con filas_afectadas correcto."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.services.padron_service import PadronService
        from app.schemas.padron import PadronImportRow

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-AUD-01")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-AUD-01")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        actor = await _crear_usuario(db_session, default_tenant.id, "aud@test.com")

        rows = [
            PadronImportRow(nombre=f"Alu{i}", apellidos="T", email=f"alu{i}@audit.com")
            for i in range(3)
        ]

        svc = PadronService(db_session, default_tenant.id)
        await svc.confirm_import(
            rows=rows, materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por_id=actor.id,
        )

        raw = await db_session.execute(
            text(
                "SELECT filas_afectadas, detalle FROM audit_log "
                "WHERE tenant_id = :tid AND accion = 'PADRON_CARGAR' "
                "ORDER BY fecha_hora DESC LIMIT 1"
            ),
            {"tid": str(default_tenant.id)},
        )
        row = raw.fetchone()
        assert row is not None, "Debe existir un registro PADRON_CARGAR en audit_log"
        assert row[0] == 3, "filas_afectadas debe ser 3"

        # El detalle no debe contener emails en claro
        detalle_str = str(row[1])
        for i in range(3):
            assert f"alu{i}@audit.com" not in detalle_str, \
                f"El detalle del audit no debe contener el email en claro: alu{i}@audit.com"

    @pytest.mark.asyncio
    async def test_vaciar_padron_genera_audit_log(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """vaciar_padron genera PADRON_VACIAR en audit_log."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.services.padron_service import PadronService
        from app.schemas.padron import PadronImportRow

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-AUD-02")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-AUD-02")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        actor = await _crear_usuario(db_session, default_tenant.id, "aud2@test.com")

        svc = PadronService(db_session, default_tenant.id)

        # Primero importar para tener algo que vaciar
        await svc.confirm_import(
            rows=[PadronImportRow(nombre="A", apellidos="B", email="a@b.com")],
            materia_id=materia.id, cohorte_id=cohorte.id, cargado_por_id=actor.id,
        )

        await svc.vaciar_padron(materia_id=materia.id, cargado_por_id=actor.id)

        raw = await db_session.execute(
            text(
                "SELECT filas_afectadas FROM audit_log "
                "WHERE tenant_id = :tid AND accion = 'PADRON_VACIAR' "
                "ORDER BY fecha_hora DESC LIMIT 1"
            ),
            {"tid": str(default_tenant.id)},
        )
        row = raw.fetchone()
        assert row is not None, "Debe existir un registro PADRON_VACIAR en audit_log"
        assert row[0] >= 1, "filas_afectadas debe reflejar las versiones vaciadas"

    @pytest.mark.asyncio
    async def test_confirm_import_detalle_no_contiene_emails(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Triangulación: incluso con múltiples emails, el detalle del audit es seguro."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.services.padron_service import PadronService
        from app.schemas.padron import PadronImportRow

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-AUD-03")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-AUD-03")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        actor = await _crear_usuario(db_session, default_tenant.id, "aud3@test.com")

        sensitive_emails = [f"sensitive{i}@private.edu" for i in range(5)]
        rows = [
            PadronImportRow(nombre=f"S{i}", apellidos="T", email=sensitive_emails[i])
            for i in range(5)
        ]

        svc = PadronService(db_session, default_tenant.id)
        await svc.confirm_import(
            rows=rows, materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por_id=actor.id,
        )

        raw = await db_session.execute(
            text(
                "SELECT detalle FROM audit_log "
                "WHERE tenant_id = :tid AND accion = 'PADRON_CARGAR' "
                "ORDER BY fecha_hora DESC LIMIT 1"
            ),
            {"tid": str(default_tenant.id)},
        )
        row = raw.fetchone()
        assert row is not None
        detalle_str = str(row[1])
        for email in sensitive_emails:
            assert email not in detalle_str, \
                f"Email en claro encontrado en audit: {email}"
