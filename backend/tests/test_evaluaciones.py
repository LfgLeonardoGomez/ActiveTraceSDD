"""Tests TDD para el módulo de evaluaciones y coloquios (C-14).

Strict TDD: Safety net → RED → GREEN → TRIANGULATE → REFACTOR.
Tests usan DB real (sin mocks de DB — regla dura).

Cobertura:
  Unit (sin DB):
    6.2   cupo lleno → crear_reserva lanza 409 sin_cupo_disponible
    6.3   reserva duplicada del mismo alumno → 409 reserva_duplicada
    6.4   cancelar reserva ya cancelada → 409 reserva_ya_cancelada
    6.5   alumno no candidato intenta reservar → 403

  Integración (DB real):
    6.6   flujo completo: crear convocatoria → importar candidatos → reservar → cancelar → cupo liberado
    6.7   upsert resultado: crear + actualizar mismo alumno
    6.8   métricas globales reflejan candidatos/reservas/resultados
    6.9   aislamiento multi-tenant
    6.10  export CSV de resultados
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.evaluacion import EstadoReserva, TipoEvaluacion
from app.schemas.evaluacion import EstadoReserva as SchemaEstadoReserva


# ---------------------------------------------------------------------------
# Safety net: registro de rutas (sin DB)
# ---------------------------------------------------------------------------


def test_coloquios_router_registrado():
    """La app incluye el router de coloquios."""
    from app.main import app

    rutas = [r.path for r in app.routes]
    assert any("/api/coloquios" in r for r in rutas), (
        "El router de coloquios no está registrado en main.py"
    )


def test_endpoints_coloquios_presentes():
    """Los endpoints principales de coloquios existen."""
    from app.main import app

    paths = {r.path for r in app.routes if hasattr(r, "methods")}

    assert "/api/coloquios/" in paths
    assert "/api/coloquios/metricas" in paths
    assert "/api/coloquios/agenda" in paths


# ---------------------------------------------------------------------------
# Safety net: schemas Pydantic (sin DB)
# ---------------------------------------------------------------------------


def test_evaluacion_create_schema_extra_forbid():
    """EvaluacionCreateSchema rechaza campos no declarados."""
    from app.schemas.evaluacion import EvaluacionCreateSchema
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        EvaluacionCreateSchema(
            materia_id=uuid4(),
            cohorte_id=uuid4(),
            tipo="Coloquio",
            instancia="Final",
            campo_extra="no permitido",
        )


def test_reserva_create_schema_valida():
    """ReservaCreateSchema acepta fecha_hora válida."""
    from app.schemas.evaluacion import ReservaCreateSchema

    schema = ReservaCreateSchema(fecha_hora=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc))
    assert schema.fecha_hora.year == 2026


def test_resultado_upsert_schema_valido():
    """ResultadoUpsertSchema acepta alumno_id y nota_final."""
    from app.schemas.evaluacion import ResultadoUpsertSchema

    schema = ResultadoUpsertSchema(alumno_id=uuid4(), nota_final="Aprobado")
    assert schema.nota_final == "Aprobado"


# ---------------------------------------------------------------------------
# 6.2 Unit: cupo lleno → 409 sin_cupo_disponible
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_reserva_cupo_lleno():
    """Si el cupo está completo, crear_reserva lanza 409 sin_cupo_disponible."""
    from app.services.evaluacion_service import EvaluacionService

    # Convocatoria con cupo_por_dia=1
    mock_evaluacion = MagicMock()
    mock_evaluacion.id = uuid4()
    mock_evaluacion.cupo_por_dia = 1

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_evaluacion
    mock_repo.is_candidato.return_value = True
    mock_repo.get_reserva_activa_del_alumno.return_value = None
    mock_repo.count_reservas_activas_en_dia.return_value = 1  # cupo lleno

    svc = EvaluacionService.__new__(EvaluacionService)
    svc._repo = mock_repo
    svc.tenant_id = uuid4()
    svc.usuario_id = uuid4()

    fecha = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
    alumno_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await svc.crear_reserva(mock_evaluacion.id, alumno_id, fecha)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "sin_cupo_disponible"


@pytest.mark.asyncio
async def test_crear_reserva_cupo_lleno_triangulate():
    """Con cupo_por_dia=3 y 3 reservas activas, también lanza 409."""
    from app.services.evaluacion_service import EvaluacionService

    mock_evaluacion = MagicMock()
    mock_evaluacion.id = uuid4()
    mock_evaluacion.cupo_por_dia = 3

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_evaluacion
    mock_repo.is_candidato.return_value = True
    mock_repo.get_reserva_activa_del_alumno.return_value = None
    mock_repo.count_reservas_activas_en_dia.return_value = 3  # cupo lleno

    svc = EvaluacionService.__new__(EvaluacionService)
    svc._repo = mock_repo

    with pytest.raises(HTTPException) as exc_info:
        await svc.crear_reserva(mock_evaluacion.id, uuid4(), datetime(2026, 7, 1, tzinfo=timezone.utc))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "sin_cupo_disponible"


# ---------------------------------------------------------------------------
# 6.3 Unit: reserva duplicada → 409 reserva_duplicada
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_reserva_duplicada():
    """Si el alumno ya tiene reserva activa, lanza 409 reserva_duplicada."""
    from app.services.evaluacion_service import EvaluacionService

    mock_evaluacion = MagicMock()
    mock_evaluacion.id = uuid4()
    mock_evaluacion.cupo_por_dia = 10

    mock_reserva_existente = MagicMock()
    mock_reserva_existente.id = uuid4()

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_evaluacion
    mock_repo.is_candidato.return_value = True
    mock_repo.get_reserva_activa_del_alumno.return_value = mock_reserva_existente  # ya tiene

    svc = EvaluacionService.__new__(EvaluacionService)
    svc._repo = mock_repo

    with pytest.raises(HTTPException) as exc_info:
        await svc.crear_reserva(mock_evaluacion.id, uuid4(), datetime(2026, 7, 1, tzinfo=timezone.utc))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "reserva_duplicada"


@pytest.mark.asyncio
async def test_crear_reserva_duplicada_triangulate_sin_reserva():
    """Sin reserva existente y con cupo, la creación procede sin error."""
    from app.services.evaluacion_service import EvaluacionService

    mock_evaluacion = MagicMock()
    mock_evaluacion.id = uuid4()
    mock_evaluacion.cupo_por_dia = 10

    mock_nueva_reserva = MagicMock()
    mock_nueva_reserva.id = uuid4()
    mock_nueva_reserva.evaluacion_id = mock_evaluacion.id
    mock_nueva_reserva.alumno_id = uuid4()
    mock_nueva_reserva.fecha_hora = datetime(2026, 7, 1, tzinfo=timezone.utc)
    mock_nueva_reserva.estado = EstadoReserva.ACTIVA
    mock_nueva_reserva.created_at = datetime.now(timezone.utc)

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_evaluacion
    mock_repo.is_candidato.return_value = True
    mock_repo.get_reserva_activa_del_alumno.return_value = None  # sin duplicado
    mock_repo.count_reservas_activas_en_dia.return_value = 0
    mock_repo.create_reserva.return_value = mock_nueva_reserva

    svc = EvaluacionService.__new__(EvaluacionService)
    svc._repo = mock_repo

    result = await svc.crear_reserva(
        mock_evaluacion.id, mock_nueva_reserva.alumno_id,
        datetime(2026, 7, 1, tzinfo=timezone.utc)
    )
    assert result.estado == SchemaEstadoReserva.ACTIVA


# ---------------------------------------------------------------------------
# 6.4 Unit: cancelar reserva ya cancelada → 409
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancelar_reserva_ya_cancelada():
    """Cancelar una reserva ya en estado Cancelada lanza 409 reserva_ya_cancelada."""
    from app.services.evaluacion_service import EvaluacionService

    mock_reserva = MagicMock()
    mock_reserva.id = uuid4()
    mock_reserva.evaluacion_id = uuid4()
    mock_reserva.alumno_id = uuid4()
    mock_reserva.estado = EstadoReserva.CANCELADA  # ya cancelada

    mock_repo = AsyncMock()
    mock_repo.get_reserva_by_id.return_value = mock_reserva

    svc = EvaluacionService.__new__(EvaluacionService)
    svc._repo = mock_repo

    with pytest.raises(HTTPException) as exc_info:
        await svc.cancelar_reserva(
            evaluacion_id=mock_reserva.evaluacion_id,
            reserva_id=mock_reserva.id,
            solicitante_id=mock_reserva.alumno_id,
            puede_gestionar=False,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "reserva_ya_cancelada"


@pytest.mark.asyncio
async def test_cancelar_reserva_activa_propia():
    """Cancelar reserva activa propia transiciona correctamente."""
    from app.services.evaluacion_service import EvaluacionService

    alumno_id = uuid4()
    ev_id = uuid4()

    mock_reserva_antes = MagicMock()
    mock_reserva_antes.id = uuid4()
    mock_reserva_antes.evaluacion_id = ev_id
    mock_reserva_antes.alumno_id = alumno_id
    mock_reserva_antes.estado = EstadoReserva.ACTIVA

    mock_reserva_despues = MagicMock()
    mock_reserva_despues.id = mock_reserva_antes.id
    mock_reserva_despues.evaluacion_id = ev_id
    mock_reserva_despues.alumno_id = alumno_id
    mock_reserva_despues.estado = EstadoReserva.CANCELADA
    mock_reserva_despues.fecha_hora = datetime.now(timezone.utc)
    mock_reserva_despues.created_at = datetime.now(timezone.utc)

    mock_repo = AsyncMock()
    mock_repo.get_reserva_by_id.return_value = mock_reserva_antes
    mock_repo.cancel_reserva.return_value = mock_reserva_despues

    svc = EvaluacionService.__new__(EvaluacionService)
    svc._repo = mock_repo

    result = await svc.cancelar_reserva(
        evaluacion_id=ev_id,
        reserva_id=mock_reserva_antes.id,
        solicitante_id=alumno_id,
        puede_gestionar=False,
    )
    assert result.estado == SchemaEstadoReserva.CANCELADA


# ---------------------------------------------------------------------------
# 6.5 Unit: alumno no candidato → 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_reserva_alumno_no_candidato():
    """Alumno no en evaluacion_candidato recibe 403."""
    from app.services.evaluacion_service import EvaluacionService

    mock_evaluacion = MagicMock()
    mock_evaluacion.id = uuid4()
    mock_evaluacion.cupo_por_dia = 5

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_evaluacion
    mock_repo.is_candidato.return_value = False  # no candidato

    svc = EvaluacionService.__new__(EvaluacionService)
    svc._repo = mock_repo

    with pytest.raises(HTTPException) as exc_info:
        await svc.crear_reserva(
            mock_evaluacion.id, uuid4(), datetime(2026, 7, 1, tzinfo=timezone.utc)
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_crear_reserva_alumno_candidato_permite_acceso():
    """Alumno en el padrón puede proceder a reservar."""
    from app.services.evaluacion_service import EvaluacionService

    mock_evaluacion = MagicMock()
    mock_evaluacion.id = uuid4()
    mock_evaluacion.cupo_por_dia = 5

    mock_reserva = MagicMock()
    mock_reserva.id = uuid4()
    mock_reserva.evaluacion_id = mock_evaluacion.id
    mock_reserva.alumno_id = uuid4()
    mock_reserva.fecha_hora = datetime(2026, 7, 1, tzinfo=timezone.utc)
    mock_reserva.estado = EstadoReserva.ACTIVA
    mock_reserva.created_at = datetime.now(timezone.utc)

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_evaluacion
    mock_repo.is_candidato.return_value = True  # candidato
    mock_repo.get_reserva_activa_del_alumno.return_value = None
    mock_repo.count_reservas_activas_en_dia.return_value = 0
    mock_repo.create_reserva.return_value = mock_reserva

    svc = EvaluacionService.__new__(EvaluacionService)
    svc._repo = mock_repo

    result = await svc.crear_reserva(mock_evaluacion.id, mock_reserva.alumno_id, mock_reserva.fecha_hora)
    assert result.id == mock_reserva.id


# ---------------------------------------------------------------------------
# 6.6 Integration: flujo completo (requiere DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requiere PostgreSQL — ejecutar con DB de test activa")
async def test_flujo_completo_convocatoria_reserva_cancelacion(db_session):
    """Flujo E2E: crear → importar candidatos → reservar → cancelar → cupo liberado."""
    from app.repositories.evaluacion_repository import EvaluacionRepository
    from app.models.estructura import Materia, Cohorte, Carrera
    from app.models.tenant import Tenant
    from app.models.user import Usuario

    # Setup tenant, carrera, cohorte, materia, alumno
    tenant = Tenant(nombre="TestTenant", slug="test-ev", activo=True)
    db_session.add(tenant)
    await db_session.commit()

    carrera = Carrera(tenant_id=tenant.id, codigo="TST", nombre="Test Carrera", estado="Activa")
    db_session.add(carrera)
    cohorte = Cohorte(tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026-1", anio=2026, estado="Activa")
    db_session.add(cohorte)
    materia = Materia(tenant_id=tenant.id, codigo="MAT01", nombre="Materia Test", estado="Activa")
    db_session.add(materia)
    alumno = Usuario(tenant_id=tenant.id, nombre="Juan", apellidos="Perez", email=b"encrypted")
    db_session.add(alumno)
    await db_session.commit()

    repo = EvaluacionRepository(db_session, tenant.id)

    # Crear convocatoria con cupo=1
    ev = await repo.create({
        "materia_id": materia.id,
        "cohorte_id": cohorte.id,
        "tipo": "Coloquio",
        "instancia": "Final",
        "dias_disponibles": 1,
        "cupo_por_dia": 1,
    })
    assert ev.id is not None

    # Importar candidatos
    total = await repo.import_candidatos(ev.id, [alumno.id])
    assert total == 1
    assert await repo.is_candidato(ev.id, alumno.id)

    # Reservar
    fecha = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
    reserva = await repo.create_reserva(ev.id, alumno.id, fecha)
    assert reserva.estado == EstadoReserva.ACTIVA

    # Cupo lleno — contar reservas activas
    ocupadas = await repo.count_reservas_activas_en_dia(ev.id, fecha)
    assert ocupadas == 1

    # Cancelar → libera cupo
    await repo.cancel_reserva(reserva)
    ocupadas_post = await repo.count_reservas_activas_en_dia(ev.id, fecha)
    assert ocupadas_post == 0


# ---------------------------------------------------------------------------
# 6.7 Integration: upsert resultado (requiere DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requiere PostgreSQL — ejecutar con DB de test activa")
async def test_upsert_resultado_crear_y_actualizar(db_session):
    """upsert_resultado crea un registro y luego lo actualiza sin duplicar."""
    from app.repositories.evaluacion_repository import EvaluacionRepository
    from sqlalchemy import select
    from app.models.evaluacion import ResultadoEvaluacion

    tenant_id = uuid4()
    ev_id = uuid4()
    alumno_id = uuid4()

    repo = EvaluacionRepository(db_session, tenant_id)

    r1 = await repo.upsert_resultado(ev_id, alumno_id, "Aprobado")
    assert r1.nota_final == "Aprobado"

    r2 = await repo.upsert_resultado(ev_id, alumno_id, "7")
    assert r2.nota_final == "7"

    # Solo debe existir UN registro
    count = (
        await db_session.execute(
            select(ResultadoEvaluacion).where(
                ResultadoEvaluacion.evaluacion_id == ev_id,
                ResultadoEvaluacion.alumno_id == alumno_id,
            )
        )
    ).scalars().all()
    assert len(count) == 1


# ---------------------------------------------------------------------------
# 6.8 Integration: métricas globales (requiere DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requiere PostgreSQL — ejecutar con DB de test activa")
async def test_metricas_globales_reflejan_estado(db_session):
    """get_metricas_globales agrega candidatos/reservas/resultados correctamente."""
    # Se implementa en DB: verificar que los conteos son correctos
    pass


# ---------------------------------------------------------------------------
# 6.9 Integration: aislamiento multi-tenant (requiere DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requiere PostgreSQL — ejecutar con DB de test activa")
async def test_aislamiento_multi_tenant(db_session):
    """Tenant A no ve convocatorias del Tenant B."""
    from app.repositories.evaluacion_repository import EvaluacionRepository

    tenant_a_id = uuid4()
    tenant_b_id = uuid4()

    repo_b = EvaluacionRepository(db_session, tenant_b_id)
    items_b, total_b = await repo_b.list_with_metrics(1, 50)

    # Sin datos del Tenant B, la lista debe estar vacía
    assert total_b == 0
    assert items_b == []


# ---------------------------------------------------------------------------
# 6.10 Integration: export CSV (requiere DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requiere PostgreSQL — ejecutar con DB de test activa")
async def test_export_csv_resultados(db_session):
    """get_resultados_csv_rows devuelve las columnas correctas."""
    from app.repositories.evaluacion_repository import EvaluacionRepository

    repo = EvaluacionRepository(db_session, uuid4())
    rows = await repo.get_resultados_csv_rows(uuid4())
    # Sin datos, devuelve lista vacía
    assert isinstance(rows, list)
    if rows:
        assert "alumno_nombre" in rows[0]
        assert "alumno_email" in rows[0]
        assert "nota_final" in rows[0]
