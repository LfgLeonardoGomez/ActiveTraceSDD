"""Tests de repositories de liquidaciones (C-18, tasks 10.2–10.4).

Requieren PostgreSQL de test (conftest.py → db_session fixture).
TDD: RED → GREEN → TRIANGULATE → REFACTOR.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.liquidaciones.exceptions import (
    LiquidacionCerradaError,
    VigenciaSolapadaError,
)
from app.modules.liquidaciones.models.enums import EstadoLiquidacion, EstadoFactura
from app.modules.liquidaciones.repositories.salario_base_repo import SalarioBaseRepository
from app.modules.liquidaciones.repositories.salario_plus_repo import SalarioPlusRepository
from app.modules.liquidaciones.repositories.materia_grupo_plus_repo import MateriaGrupoPlusRepository
from app.modules.liquidaciones.repositories.liquidacion_repo import LiquidacionRepository
from app.modules.liquidaciones.repositories.factura_repo import FacturaRepository


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def tenant_id(db_session, default_tenant):
    return default_tenant.id


@pytest_asyncio.fixture
async def cohorte_fixture(db_session, default_tenant):
    """Crea una Carrera + Cohorte para usar en tests de liquidación."""
    from app.models.estructura import Carrera, Cohorte  # noqa: PLC0415
    carrera = Carrera(
        tenant_id=default_tenant.id,
        codigo="ING",
        nombre="Ingeniería",
    )
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    cohorte = Cohorte(
        tenant_id=default_tenant.id,
        carrera_id=carrera.id,
        nombre="2024",
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)
    return cohorte


@pytest_asyncio.fixture
async def materia_fixture(db_session, default_tenant, cohorte_fixture):
    """Crea una Materia para tests."""
    from app.models.estructura import Materia  # noqa: PLC0415
    materia = Materia(
        tenant_id=default_tenant.id,
        codigo="PROG1",
        nombre="Programación I",
    )
    db_session.add(materia)
    await db_session.commit()
    await db_session.refresh(materia)
    return materia


@pytest_asyncio.fixture
async def usuario_fixture(db_session, default_tenant):
    """Crea un usuario docente para tests."""
    from app.models.user import Usuario  # noqa: PLC0415
    from app.core.encryption import encrypt_pii  # noqa: PLC0415
    usuario = Usuario(
        tenant_id=default_tenant.id,
        email=encrypt_pii("docente@test.com"),
        email_hash="hash_docente",
        nombre="Juan",
        apellido="Docente",
        facturador=False,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


@pytest_asyncio.fixture
async def usuario_facturante(db_session, default_tenant):
    """Crea un usuario facturante para tests."""
    from app.models.user import Usuario  # noqa: PLC0415
    from app.core.encryption import encrypt_pii  # noqa: PLC0415
    usuario = Usuario(
        tenant_id=default_tenant.id,
        email=encrypt_pii("facturante@test.com"),
        email_hash="hash_facturante",
        nombre="Maria",
        apellido="Facturante",
        facturador=True,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


# ─────────────────────────────────────────────────────────────────────────────
# 10.2 Tests de SalarioBase
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_salario_base_crear(db_session: AsyncSession, tenant_id):
    """CRUD básico: crear y recuperar."""
    repo = SalarioBaseRepository(db_session, tenant_id)
    sb = await repo.create_with_overlap_check(
        rol="PROFESOR",
        monto=Decimal("100000"),
        desde=date(2026, 1, 1),
        hasta=None,
    )
    assert sb.id is not None
    assert sb.rol == "PROFESOR"
    assert sb.monto == Decimal("100000")


@pytest.mark.asyncio
async def test_salario_base_overlap_rechazado(db_session: AsyncSession, tenant_id):
    """Solapamiento de vigencia → VigenciaSolapadaError."""
    repo = SalarioBaseRepository(db_session, tenant_id)
    await repo.create_with_overlap_check(
        rol="PROFESOR", monto=Decimal("100000"), desde=date(2026, 1, 1), hasta=None
    )
    with pytest.raises(VigenciaSolapadaError):
        await repo.create_with_overlap_check(
            rol="PROFESOR", monto=Decimal("120000"), desde=date(2026, 6, 1), hasta=None
        )


@pytest.mark.asyncio
async def test_salario_base_find_vigente(db_session: AsyncSession, tenant_id):
    """find_vigente devuelve la fila correcta para un período."""
    repo = SalarioBaseRepository(db_session, tenant_id)
    await repo.create_with_overlap_check(
        rol="PROFESOR", monto=Decimal("100000"),
        desde=date(2026, 1, 1), hasta=date(2026, 5, 31)
    )
    await repo.create_with_overlap_check(
        rol="PROFESOR", monto=Decimal("120000"),
        desde=date(2026, 6, 1), hasta=None
    )
    vigente_ene = await repo.find_vigente("PROFESOR", "2026-03")
    assert vigente_ene.monto == Decimal("100000")

    vigente_jun = await repo.find_vigente("PROFESOR", "2026-07")
    assert vigente_jun.monto == Decimal("120000")


@pytest.mark.asyncio
async def test_salario_base_find_vigente_none(db_session: AsyncSession, tenant_id):
    """Sin SalarioBase vigente → None."""
    repo = SalarioBaseRepository(db_session, tenant_id)
    result = await repo.find_vigente("NEXO", "2026-03")
    assert result is None


@pytest.mark.asyncio
async def test_salario_base_soft_delete(db_session: AsyncSession, tenant_id):
    """Soft delete: deleted_at se setea, fila no aparece en list."""
    repo = SalarioBaseRepository(db_session, tenant_id)
    sb = await repo.create_with_overlap_check(
        rol="TUTOR", monto=Decimal("80000"), desde=date(2026, 1, 1), hasta=None
    )
    eliminado = await repo.delete(sb.id)
    assert eliminado is True
    lista = await repo.list(rol="TUTOR")
    assert len(lista) == 0


# ─────────────────────────────────────────────────────────────────────────────
# 10.3 Tests de SalarioPlus
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_salario_plus_crear(db_session: AsyncSession, tenant_id):
    """Crear SalarioPlus sin tope."""
    repo = SalarioPlusRepository(db_session, tenant_id)
    sp = await repo.create_with_overlap_check(
        grupo="PROG", rol="PROFESOR", monto=Decimal("15000"),
        desde=date(2026, 1, 1), hasta=None
    )
    assert sp.grupo == "PROG"
    assert sp.tope_acumulacion is None


@pytest.mark.asyncio
async def test_salario_plus_overlap_mismo_grupo_rol(db_session: AsyncSession, tenant_id):
    """Overlap por (grupo, rol) → VigenciaSolapadaError."""
    repo = SalarioPlusRepository(db_session, tenant_id)
    await repo.create_with_overlap_check(
        grupo="PROG", rol="PROFESOR", monto=Decimal("15000"),
        desde=date(2026, 1, 1), hasta=None
    )
    with pytest.raises(VigenciaSolapadaError):
        await repo.create_with_overlap_check(
            grupo="PROG", rol="PROFESOR", monto=Decimal("18000"),
            desde=date(2026, 6, 1), hasta=None
        )


@pytest.mark.asyncio
async def test_salario_plus_distintos_grupos_no_solapan(db_session: AsyncSession, tenant_id):
    """Grupos distintos: no hay overlap entre sí."""
    repo = SalarioPlusRepository(db_session, tenant_id)
    await repo.create_with_overlap_check(
        grupo="PROG", rol="PROFESOR", monto=Decimal("15000"),
        desde=date(2026, 1, 1), hasta=None
    )
    # BD con mismo rol y misma vigencia → OK porque grupo distinto
    sp_bd = await repo.create_with_overlap_check(
        grupo="BD", rol="PROFESOR", monto=Decimal("8000"),
        desde=date(2026, 1, 1), hasta=None
    )
    assert sp_bd.grupo == "BD"


@pytest.mark.asyncio
async def test_salario_plus_con_tope(db_session: AsyncSession, tenant_id):
    """Crear SalarioPlus con tope de acumulación."""
    repo = SalarioPlusRepository(db_session, tenant_id)
    sp = await repo.create_with_overlap_check(
        grupo="BD", rol="TUTOR", monto=Decimal("8000"),
        desde=date(2026, 1, 1), hasta=None,
        tope_acumulacion=Decimal("3"),
    )
    assert sp.tope_acumulacion == Decimal("3")


# ─────────────────────────────────────────────────────────────────────────────
# 10.4 Tests de MateriaGrupoPlus
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mgp_crear(db_session: AsyncSession, tenant_id, materia_fixture):
    """Crear mapeo materia → grupo."""
    repo = MateriaGrupoPlusRepository(db_session, tenant_id)
    mgp = await repo.create_with_overlap_check(
        materia_id=materia_fixture.id, grupo="PROG",
        desde=date(2026, 1, 1), hasta=None
    )
    assert mgp.grupo == "PROG"


@pytest.mark.asyncio
async def test_mgp_overlap_misma_materia(db_session: AsyncSession, tenant_id, materia_fixture):
    """Overlap para la misma materia → VigenciaSolapadaError."""
    repo = MateriaGrupoPlusRepository(db_session, tenant_id)
    await repo.create_with_overlap_check(
        materia_id=materia_fixture.id, grupo="PROG",
        desde=date(2026, 1, 1), hasta=None
    )
    with pytest.raises(VigenciaSolapadaError):
        await repo.create_with_overlap_check(
            materia_id=materia_fixture.id, grupo="BD",
            desde=date(2026, 6, 1), hasta=None
        )


@pytest.mark.asyncio
async def test_mgp_recategorizacion_preserva_historial(
    db_session: AsyncSession, tenant_id, materia_fixture
):
    """Recategorizar: fila anterior se cierra, nueva coexiste."""
    repo = MateriaGrupoPlusRepository(db_session, tenant_id)
    mgp1 = await repo.create_with_overlap_check(
        materia_id=materia_fixture.id, grupo="PROG",
        desde=date(2026, 1, 1), hasta=None
    )
    # Cerrar la vigencia anterior
    await repo.update(mgp1.id, {"hasta": date(2026, 5, 31)})
    # Crear nueva vigencia
    mgp2 = await repo.create_with_overlap_check(
        materia_id=materia_fixture.id, grupo="PROG_AVANZADA",
        desde=date(2026, 6, 1), hasta=None
    )
    # El grupo vigente en 2026-03 sigue siendo PROG
    grupo_marzo = await repo.find_grupo_vigente(materia_fixture.id, "2026-03")
    assert grupo_marzo == "PROG"
    # El grupo vigente en 2026-07 es PROG_AVANZADA
    grupo_julio = await repo.find_grupo_vigente(materia_fixture.id, "2026-07")
    assert grupo_julio == "PROG_AVANZADA"


@pytest.mark.asyncio
async def test_mgp_find_grupo_vigente_none(
    db_session: AsyncSession, tenant_id, materia_fixture
):
    """Sin mapeo vigente → None."""
    repo = MateriaGrupoPlusRepository(db_session, tenant_id)
    result = await repo.find_grupo_vigente(materia_fixture.id, "2026-03")
    assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# Tests de LiquidacionRepository — guard de inmutabilidad (D3)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_liquidacion_guard_cerrada_update(
    db_session: AsyncSession, tenant_id, cohorte_fixture, usuario_fixture
):
    """update sobre fila Cerrada → LiquidacionCerradaError."""
    repo = LiquidacionRepository(db_session, tenant_id)
    # Crear fila directamente como Cerrada
    filas = await repo.bulk_create_cerradas([{
        "cohorte_id": cohorte_fixture.id,
        "periodo": "2026-03",
        "usuario_id": usuario_fixture.id,
        "rol": "PROFESOR",
        "monto_base": Decimal("100000"),
        "monto_plus": Decimal("15000"),
        "total": Decimal("115000"),
        "es_nexo": False,
        "excluido_por_factura": False,
        "estado": EstadoLiquidacion.CERRADA,
        "cerrada_at": datetime.now(timezone.utc),
        "cerrada_por_usuario_id": usuario_fixture.id,
    }])
    assert len(filas) == 1

    with pytest.raises(LiquidacionCerradaError):
        await repo.update(filas[0].id, {"monto_base": Decimal("999")})


@pytest.mark.asyncio
async def test_liquidacion_guard_cerrada_delete(
    db_session: AsyncSession, tenant_id, cohorte_fixture, usuario_fixture
):
    """delete sobre fila Cerrada → LiquidacionCerradaError."""
    repo = LiquidacionRepository(db_session, tenant_id)
    filas = await repo.bulk_create_cerradas([{
        "cohorte_id": cohorte_fixture.id,
        "periodo": "2026-04",
        "usuario_id": usuario_fixture.id,
        "rol": "TUTOR",
        "monto_base": Decimal("80000"),
        "monto_plus": Decimal("0"),
        "total": Decimal("80000"),
        "es_nexo": False,
        "excluido_por_factura": False,
        "estado": EstadoLiquidacion.CERRADA,
        "cerrada_at": datetime.now(timezone.utc),
        "cerrada_por_usuario_id": usuario_fixture.id,
    }])
    with pytest.raises(LiquidacionCerradaError):
        await repo.delete(filas[0].id)
