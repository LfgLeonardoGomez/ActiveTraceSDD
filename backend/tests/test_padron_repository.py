"""Tests TDD para PadronRepository (C-09).

Strict TDD: RED → GREEN → TRIANGULATE.
Tests usan DB real (sin mocks — regla dura).

Safety net: no hay código previo de padrón — no hay baseline que romper.
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


# ---------------------------------------------------------------------------
# Helpers de fixtures locales
# ---------------------------------------------------------------------------


async def _crear_materia(db_session: AsyncSession, tenant_id, codigo: str = "MAT-01"):
    """Crea una materia mínima para los tests."""
    from app.models.estructura import Materia
    m = Materia(
        tenant_id=tenant_id,
        codigo=codigo,
        nombre=f"Materia {codigo}",
        estado="Activa",
    )
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


async def _crear_carrera(db_session: AsyncSession, tenant_id, codigo: str = "CAR-01"):
    from app.models.estructura import Carrera
    c = Carrera(
        tenant_id=tenant_id,
        codigo=codigo,
        nombre=f"Carrera {codigo}",
        estado="Activa",
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


async def _crear_cohorte(db_session: AsyncSession, tenant_id, carrera_id):
    from app.models.estructura import Cohorte
    c = Cohorte(
        tenant_id=tenant_id,
        carrera_id=carrera_id,
        nombre="AGO-2025",
        anio=2025,
        estado="Activa",
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


async def _crear_usuario(db_session: AsyncSession, tenant_id, email: str = "doc@test.com"):
    from app.repositories.usuarios import UsuarioRepository
    repo = UsuarioRepository(db_session, tenant_id)
    return await repo.create(
        nombre="Docente",
        apellidos="Test",
        email=email,
        estado="Activo",
    )


# ---------------------------------------------------------------------------
# Grupo 1: Creación y activación de versiones
# ---------------------------------------------------------------------------


class TestVersionPadronCRUD:
    """Task 2.1-2.3 RED → GREEN → TRIANGULATE."""

    @pytest.mark.asyncio
    async def test_crear_version_padron(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 2.1: crear versión de padrón → persiste con activa=True."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa: register with Base
        from app.repositories.padron_repository import PadronRepository

        materia = await _crear_materia(db_session, default_tenant.id)
        carrera = await _crear_carrera(db_session, default_tenant.id)
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        usuario = await _crear_usuario(db_session, default_tenant.id)

        repo = PadronRepository(db_session, default_tenant.id)
        version = await repo.crear_version(
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            cargado_por=usuario.id,
        )

        assert version.id is not None
        assert version.materia_id == materia.id
        assert version.cohorte_id == cohorte.id
        assert version.tenant_id == default_tenant.id
        assert version.activa is False
        assert version.origen == "manual"

    @pytest.mark.asyncio
    async def test_activar_version_desactiva_anterior(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 2.3: activar nueva versión → la anterior queda activa=False."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.repositories.padron_repository import PadronRepository

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-02")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-02")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        usuario = await _crear_usuario(db_session, default_tenant.id, "doc2@test.com")

        repo = PadronRepository(db_session, default_tenant.id)

        # Crear y activar primera versión
        v1 = await repo.crear_version(
            materia_id=materia.id, cohorte_id=cohorte.id, cargado_por=usuario.id
        )
        await repo.activar_version(v1.id, materia.id, cohorte.id)

        version_activa = await repo.get_active_version(materia.id, cohorte.id)
        assert version_activa is not None
        assert version_activa.id == v1.id

        # Crear y activar segunda versión
        v2 = await repo.crear_version(
            materia_id=materia.id, cohorte_id=cohorte.id, cargado_por=usuario.id
        )
        await repo.activar_version(v2.id, materia.id, cohorte.id)

        version_activa_nueva = await repo.get_active_version(materia.id, cohorte.id)
        assert version_activa_nueva is not None
        assert version_activa_nueva.id == v2.id

        # La primera versión debe estar inactiva (pero NO borrada)
        v1_raw = await db_session.execute(
            text("SELECT activa, deleted_at FROM versiones_padron WHERE id = :vid"),
            {"vid": str(v1.id)},
        )
        row = v1_raw.fetchone()
        assert row is not None
        assert row[0] is False, "v1 debe estar inactiva"
        assert row[1] is None, "v1 NO debe estar borrada (historial preservado)"

    @pytest.mark.asyncio
    async def test_get_active_version_sin_historial(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 2.2: get_active_version sin versión previa → None."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.repositories.padron_repository import PadronRepository

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-03")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-03")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)

        repo = PadronRepository(db_session, default_tenant.id)
        result = await repo.get_active_version(materia.id, cohorte.id)
        assert result is None


# ---------------------------------------------------------------------------
# Grupo 2: EntradaPadron — cifrado y lookup
# ---------------------------------------------------------------------------


class TestEntradaPadronCifrado:
    """Task 2.4 + cifrado RED → GREEN → TRIANGULATE."""

    @pytest.mark.asyncio
    async def test_crear_entradas_padron_email_cifrado(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED: email de EntradaPadron cifrado en DB, descifrado al leer."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.repositories.padron_repository import PadronRepository

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-04")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-04")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        usuario = await _crear_usuario(db_session, default_tenant.id, "doc4@test.com")

        repo = PadronRepository(db_session, default_tenant.id)
        version = await repo.crear_version(
            materia_id=materia.id, cohorte_id=cohorte.id, cargado_por=usuario.id
        )

        entrada = await repo.crear_entrada(
            version_id=version.id,
            nombre="Juan",
            apellidos="Perez",
            email="juan.perez@alumno.com",
            comision="A",
            regional="Buenos Aires",
            usuario_id=None,
        )

        # Al leer vía repositorio: texto plano
        assert entrada.email == "juan.perez@alumno.com"

        # En DB: ciphertext
        raw = await db_session.execute(
            text("SELECT email FROM entradas_padron WHERE id = :eid"),
            {"eid": str(entrada.id)},
        )
        row = raw.fetchone()
        assert row is not None
        assert row[0] != "juan.perez@alumno.com", "email debe estar cifrado en DB"
        assert len(row[0]) > 50, "ciphertext es largo (base64 AES-GCM)"

    @pytest.mark.asyncio
    async def test_get_entradas_by_version(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: get_entradas_by_version devuelve entradas descifradas."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.repositories.padron_repository import PadronRepository

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-05")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-05")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        usuario = await _crear_usuario(db_session, default_tenant.id, "doc5@test.com")

        repo = PadronRepository(db_session, default_tenant.id)
        version = await repo.crear_version(
            materia_id=materia.id, cohorte_id=cohorte.id, cargado_por=usuario.id
        )

        for i in range(3):
            await repo.crear_entrada(
                version_id=version.id,
                nombre=f"Alumno{i}",
                apellidos="Test",
                email=f"alumno{i}@test.com",
                comision="B",
                regional="",
                usuario_id=None,
            )

        entradas = await repo.get_entradas_by_version(version.id)
        assert len(entradas) == 3
        emails = {e.email for e in entradas}
        assert "alumno0@test.com" in emails
        assert "alumno2@test.com" in emails

    @pytest.mark.asyncio
    async def test_email_no_en_logs_audit(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: email en claro NO debe aparecer en detalle de AuditLog."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.core.audit import record_audit, AuditAction

        await record_audit(
            db_session,
            actor_id=uuid4(),
            tenant_id=default_tenant.id,
            accion=AuditAction.PADRON_CARGAR,
            filas_afectadas=5,
            detalle={"materia_id": str(uuid4()), "origen": "manual"},
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
        detalle_str = str(row[0])
        assert "@" not in detalle_str or "alumno" not in detalle_str.lower(), \
            "El detalle del audit NO debe contener emails en claro"


# ---------------------------------------------------------------------------
# Grupo 3: Aislamiento multi-tenant
# ---------------------------------------------------------------------------


class TestPadronAislamientoMultiTenant:
    """Task 2.5 + 9.1: aislamiento entre tenants."""

    @pytest.mark.asyncio
    async def test_tenant_b_no_ve_padron_tenant_a(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Tenant B no puede ver versiones del padrón de Tenant A."""
        from app.models.tenant import Tenant
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.repositories.padron_repository import PadronRepository

        tenant_b = Tenant(nombre="Tenant B Padron", slug="tenant-b-padron", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-06")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-06")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        usuario = await _crear_usuario(db_session, default_tenant.id, "doc6@test.com")

        repo_a = PadronRepository(db_session, default_tenant.id)
        v_a = await repo_a.crear_version(
            materia_id=materia.id, cohorte_id=cohorte.id, cargado_por=usuario.id
        )
        await repo_a.activar_version(v_a.id, materia.id, cohorte.id)

        # Tenant B con el mismo materia_id no debe ver la versión de Tenant A
        repo_b = PadronRepository(db_session, tenant_b.id)
        version_b = await repo_b.get_active_version(materia.id, cohorte.id)
        assert version_b is None


# ---------------------------------------------------------------------------
# Grupo 4: Soft delete scope-isolated
# ---------------------------------------------------------------------------


class TestPadronSoftDeleteScopeIsolated:
    """Task 5.2: vaciar solo afecta el scope del actor."""

    @pytest.mark.asyncio
    async def test_soft_delete_versiones_scope_isolated(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Vaciar padrón: solo elimina versiones del usuario ejecutor."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.repositories.padron_repository import PadronRepository

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-07")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-07")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        usuario_a = await _crear_usuario(db_session, default_tenant.id, "docA@test.com")
        usuario_b = await _crear_usuario(db_session, default_tenant.id, "docB@test.com")

        repo = PadronRepository(db_session, default_tenant.id)

        # Versión de usuario A
        v_a = await repo.crear_version(
            materia_id=materia.id, cohorte_id=cohorte.id, cargado_por=usuario_a.id
        )
        await repo.crear_entrada(
            version_id=v_a.id, nombre="A1", apellidos="X",
            email="a1@test.com", usuario_id=None
        )

        # Versión de usuario B
        v_b = await repo.crear_version(
            materia_id=materia.id, cohorte_id=cohorte.id, cargado_por=usuario_b.id
        )
        await repo.crear_entrada(
            version_id=v_b.id, nombre="B1", apellidos="Y",
            email="b1@test.com", usuario_id=None
        )

        # Vaciar scope de usuario_a para esta materia
        deleted = await repo.soft_delete_all_versions(
            materia_id=materia.id, cargado_por=usuario_a.id
        )
        assert deleted >= 1

        # Versión de A debe estar soft-deleted
        raw_a = await db_session.execute(
            text("SELECT deleted_at FROM versiones_padron WHERE id = :vid"),
            {"vid": str(v_a.id)},
        )
        row_a = raw_a.fetchone()
        assert row_a[0] is not None, "v_a debe estar soft-deleted"

        # Versión de B debe seguir intacta
        raw_b = await db_session.execute(
            text("SELECT deleted_at FROM versiones_padron WHERE id = :vid"),
            {"vid": str(v_b.id)},
        )
        row_b = raw_b.fetchone()
        assert row_b[0] is None, "v_b NO debe ser afectada por el vaciado de usuario_a"
