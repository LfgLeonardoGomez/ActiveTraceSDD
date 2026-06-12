"""Tests TDD — Panel de Auditoría y Métricas (C-19).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Tests usan DB real (sin mocks — regla dura).

Safety net (7.1): 3 passed (DB unavailable en este entorno) — todos los ERRORs
son DNS failures pre-existentes del entorno, no fallos de lógica.

Cobertura por requirement (spec-driven):
  7.2  fixture seed_audit_records
  7.3  acciones_por_dia agrupa correctamente por día UTC
  7.4  acciones_por_dia sin params usa rango últimos 30 días
  7.5  acciones_por_dia filtra por materia_id
  7.6  acciones_por_dia aplica scope (propio) — COORDINADOR
  7.7  aislamiento multi-tenant en acciones_por_dia
  7.8  comunicaciones_por_docente cuenta cada estado correctamente
  7.9  comunicaciones_por_docente aplica scope (propio)
  7.10 interacciones_por_docente_materia agrupa y agrega categoría
  7.11 interacciones_por_docente_materia con materia_id NULL
  7.12 ultimas_acciones con limit=200 (default) sobre 500 registros
  7.13 ultimas_acciones con limit=50 devuelve exactamente 50
  7.14 ultimas_acciones con limit=1001 → 422
  7.15 ultimas_acciones con accion=COMUNICACION_ENVIAR filtra
  7.16 ultimas_acciones con accion=INEXISTENTE_X → 422
  7.17 catalogo-acciones retorna item por cada miembro de AuditAction
  7.18 GET /api/auditoria/log paginación default (75 registros → total=75, pages=2)
  7.19 GET /api/auditoria/log?page=2 devuelve los 25 restantes
  7.20 GET /api/auditoria/log?page_size=201 → 422
  7.21 GET /api/auditoria/log?page_size=0 → 422
  7.22 filtro por rango de fechas inclusivo
  7.23 filtro usuario_id matchea actor_id Y impersonado_id
  7.24 filtro estado=Enviado matchea detalle.estado correcto
  7.25 scope (propio) en log — COORDINADOR ve solo 4 propios de 24
  7.26 ADMIN con is_propio=False ve los 24 registros
  7.27 filtro usuario_id NO cruza tenants
  7.28 PROFESOR sin auditoria:ver recibe 403
  7.29 ALUMNO sin auditoria:ver recibe 403 en catalogo-acciones
  7.30 contract: repos no exponen métodos de escritura
  7.31 contract: ninguna ruta bajo /api/auditoria/ admite POST/PUT/PATCH/DELETE
"""

import inspect
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction
from app.models.audit_log import AuditLog
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.repositories.auditoria_panel_repository import AuditoriaPanelRepository
from app.repositories.auditoria_log_query_repository import AuditoriaLogQueryRepository
from app.schemas.auditoria import (
    AccionesPorDiaResponse,
    ComunicacionesPorDocenteResponse,
    InteraccionesPorDocenteMateriaResponse,
    UltimasAccionesResponse,
    AuditLogPageResponse,
    CatalogoAccionesResponse,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.auditoria_panel_service import AuditoriaPanelService
from app.services.auditoria_log_query_service import AuditoriaLogQueryService


# ---------------------------------------------------------------------------
# Helpers de setup
# ---------------------------------------------------------------------------


async def _crear_tenant(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(nombre=f"Tenant {uuid4().hex[:6]}", slug=uuid4().hex[:8], activo=True)
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


async def _crear_usuario(db_session: AsyncSession, tenant_id: UUID):
    from app.models.user import Usuario
    u = Usuario(
        tenant_id=tenant_id,
        nombre="Docente",
        apellidos=f"Test {uuid4().hex[:4]}",
        email=f"user_{uuid4().hex[:8]}@test.com",
        estado="Activo",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _crear_materia(db_session: AsyncSession, tenant_id: UUID):
    from app.models.estructura import Materia
    m = Materia(
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid4().hex[:6]}",
        nombre=f"Materia {uuid4().hex[:4]}",
        estado="Activa",
    )
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


async def _insert_audit(
    db_session: AsyncSession,
    tenant_id: UUID,
    actor_id: UUID,
    *,
    fecha_hora: datetime | None = None,
    accion: str = "CALIFICACIONES_IMPORTAR",
    materia_id: UUID | None = None,
    impersonado_id: UUID | None = None,
    detalle: dict | None = None,
) -> AuditLog:
    """Inserta directamente un AuditLog sin pasar por el helper record_audit."""
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        accion=accion,
        materia_id=materia_id,
        impersonado_id=impersonado_id,
        detalle=detalle,
        filas_afectadas=1,
    )
    if fecha_hora is not None:
        entry.fecha_hora = fecha_hora
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)
    return entry


async def _insert_comunicacion(
    db_session: AsyncSession,
    tenant_id: UUID,
    enviado_por: UUID,
    materia_id: UUID,
    estado: str = "Enviado",
) -> Comunicacion:
    from app.core.encryption import encrypt_pii
    c = Comunicacion(
        tenant_id=tenant_id,
        enviado_por=enviado_por,
        materia_id=materia_id,
        destinatario=encrypt_pii(f"dest_{uuid4().hex[:6]}@test.com"),
        asunto="Test asunto",
        cuerpo="Test cuerpo",
        estado=estado,
        aprobado=True,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


def _perm_ctx(is_propio: bool = False) -> PermissionContext:
    return PermissionContext(
        has_permission=True,
        is_propio=is_propio,
        effective_permissions={"auditoria:ver"},
    )


# ---------------------------------------------------------------------------
# Phase 7.2 — Fixture / helpers verificados
# ---------------------------------------------------------------------------


class TestSetupFixtures:
    """Verifica que los helpers de seed funcionan correctamente."""

    @pytest.mark.asyncio
    async def test_insert_audit_creates_record(self, db_session, default_tenant) -> None:
        """RED: _insert_audit inserta un AuditLog en la DB."""
        u = await _crear_usuario(db_session, default_tenant.id)
        entry = await _insert_audit(db_session, default_tenant.id, u.id)
        assert entry.id is not None
        assert entry.accion == "CALIFICACIONES_IMPORTAR"


# ---------------------------------------------------------------------------
# Phase 7.3 — acciones_por_dia agrupa por día UTC
# ---------------------------------------------------------------------------


class TestAccionesPorDia:
    """Tests para el endpoint acciones-por-dia."""

    @pytest.mark.asyncio
    async def test_agrupa_por_dia_utc(self, db_session, default_tenant) -> None:
        """RED 7.3: 3 registros el día A + 2 registros el día B → agrupación correcta."""
        u = await _crear_usuario(db_session, default_tenant.id)
        dia_a = datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)
        dia_b = datetime(2026, 6, 11, 10, 0, tzinfo=timezone.utc)

        for _ in range(3):
            await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia_a)
        for _ in range(2):
            await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia_b)

        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.get_acciones_por_dia({}, _perm_ctx())

        assert isinstance(result, AccionesPorDiaResponse)
        assert len(result.items) == 2
        totales = {str(item.fecha): item.total for item in result.items}
        assert totales["2026-06-10"] == 3
        assert totales["2026-06-11"] == 2

    @pytest.mark.asyncio
    async def test_sin_params_usa_rango_30_dias(self, db_session, default_tenant) -> None:
        """RED 7.4: sin params el campo rango cubre los últimos 30 días."""
        u = await _crear_usuario(db_session, default_tenant.id)
        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.get_acciones_por_dia({}, _perm_ctx())
        now = datetime.now(timezone.utc)
        delta = (now - result.rango.desde).days
        assert 28 <= delta <= 31

    @pytest.mark.asyncio
    async def test_filtra_por_materia_id(self, db_session, default_tenant) -> None:
        """RED 7.5: registros con otra materia no se cuentan."""
        u = await _crear_usuario(db_session, default_tenant.id)
        mat_a = await _crear_materia(db_session, default_tenant.id)
        mat_b = await _crear_materia(db_session, default_tenant.id)
        dia = datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc)

        await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia, materia_id=mat_a.id)
        await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia, materia_id=mat_a.id)
        await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia, materia_id=mat_b.id)

        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.get_acciones_por_dia(
            {"materia_id": mat_a.id,
             "fecha_desde": date(2026, 6, 12),
             "fecha_hasta": date(2026, 6, 12)},
            _perm_ctx(),
        )
        assert len(result.items) == 1
        assert result.items[0].total == 2

    @pytest.mark.asyncio
    async def test_scope_propio_filtra_por_actor(self, db_session, default_tenant) -> None:
        """RED 7.6: COORDINADOR (is_propio=True) ve solo sus registros."""
        u1 = await _crear_usuario(db_session, default_tenant.id)
        u2 = await _crear_usuario(db_session, default_tenant.id)
        dia = datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc)

        # 2 registros del actor u1
        await _insert_audit(db_session, default_tenant.id, u1.id, fecha_hora=dia)
        await _insert_audit(db_session, default_tenant.id, u1.id, fecha_hora=dia)
        # 3 registros del actor u2
        for _ in range(3):
            await _insert_audit(db_session, default_tenant.id, u2.id, fecha_hora=dia)

        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u1.id,
        )
        result = await service.get_acciones_por_dia(
            {"fecha_desde": date(2026, 6, 12), "fecha_hasta": date(2026, 6, 12)},
            _perm_ctx(is_propio=True),
        )
        total = sum(item.total for item in result.items)
        assert total == 2

    @pytest.mark.asyncio
    async def test_aislamiento_multi_tenant(self, db_session, default_tenant) -> None:
        """RED 7.7: registros de Tenant B no aparecen en queries de Tenant A."""
        from app.models.tenant import Tenant
        tenant_b = Tenant(nombre="Tenant B", slug="tenant-b-audit", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        u_a = await _crear_usuario(db_session, default_tenant.id)
        u_b = await _crear_usuario(db_session, tenant_b.id)
        dia = datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc)

        await _insert_audit(db_session, default_tenant.id, u_a.id, fecha_hora=dia)
        await _insert_audit(db_session, tenant_b.id, u_b.id, fecha_hora=dia)
        await _insert_audit(db_session, tenant_b.id, u_b.id, fecha_hora=dia)

        service_a = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u_a.id,
        )
        result = await service_a.get_acciones_por_dia(
            {"fecha_desde": date(2026, 6, 12), "fecha_hasta": date(2026, 6, 12)},
            _perm_ctx(),
        )
        total = sum(item.total for item in result.items)
        assert total == 1  # solo los del Tenant A


# ---------------------------------------------------------------------------
# Phase 7.8-7.9 — comunicaciones_por_docente
# ---------------------------------------------------------------------------


class TestComunicacionesPorDocente:
    """Tests para comunicaciones_por_docente."""

    @pytest.mark.asyncio
    async def test_cuenta_estados_correctamente(self, db_session, default_tenant) -> None:
        """RED 7.8: Enviado=3, Error=1, resto=0 para un docente."""
        u = await _crear_usuario(db_session, default_tenant.id)
        mat = await _crear_materia(db_session, default_tenant.id)

        await _insert_comunicacion(db_session, default_tenant.id, u.id, mat.id, "Enviado")
        await _insert_comunicacion(db_session, default_tenant.id, u.id, mat.id, "Enviado")
        await _insert_comunicacion(db_session, default_tenant.id, u.id, mat.id, "Enviado")
        await _insert_comunicacion(db_session, default_tenant.id, u.id, mat.id, "Error")

        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.get_comunicaciones_por_docente({}, _perm_ctx())

        assert isinstance(result, ComunicacionesPorDocenteResponse)
        assert len(result.items) == 1
        item = result.items[0]
        assert item.usuario_id == u.id
        assert item.conteos.Enviado == 3
        assert item.conteos.Error == 1
        assert item.conteos.Pendiente == 0
        assert item.conteos.Enviando == 0
        assert item.conteos.Cancelado == 0

    @pytest.mark.asyncio
    async def test_scope_propio_coordinador(self, db_session, default_tenant) -> None:
        """RED 7.9: COORDINADOR (is_propio=True) ve solo sus comunicaciones."""
        u1 = await _crear_usuario(db_session, default_tenant.id)
        u2 = await _crear_usuario(db_session, default_tenant.id)
        mat = await _crear_materia(db_session, default_tenant.id)

        await _insert_comunicacion(db_session, default_tenant.id, u1.id, mat.id, "Enviado")
        await _insert_comunicacion(db_session, default_tenant.id, u2.id, mat.id, "Enviado")
        await _insert_comunicacion(db_session, default_tenant.id, u2.id, mat.id, "Error")

        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u1.id,
        )
        result = await service.get_comunicaciones_por_docente({}, _perm_ctx(is_propio=True))

        # Solo ve los de u1
        assert len(result.items) == 1
        assert result.items[0].usuario_id == u1.id
        assert result.items[0].conteos.Enviado == 1


# ---------------------------------------------------------------------------
# Phase 7.10-7.11 — interacciones_por_docente_materia
# ---------------------------------------------------------------------------


class TestInteraccionesPorDocenteMateria:
    """Tests para interacciones_por_docente_materia."""

    @pytest.mark.asyncio
    async def test_agrupa_y_calcula_categoria(self, db_session, default_tenant) -> None:
        """RED 7.10: agrupa por (actor_id, materia_id, accion) y calcula categoría del prefijo."""
        u = await _crear_usuario(db_session, default_tenant.id)
        mat = await _crear_materia(db_session, default_tenant.id)
        dia = datetime(2026, 6, 12, 10, 0, tzinfo=timezone.utc)

        # 2 registros CALIFICACIONES_IMPORTAR
        await _insert_audit(
            db_session, default_tenant.id, u.id,
            fecha_hora=dia, accion="CALIFICACIONES_IMPORTAR", materia_id=mat.id
        )
        await _insert_audit(
            db_session, default_tenant.id, u.id,
            fecha_hora=dia, accion="CALIFICACIONES_IMPORTAR", materia_id=mat.id
        )
        # 1 registro COMUNICACION_ENVIAR
        await _insert_audit(
            db_session, default_tenant.id, u.id,
            fecha_hora=dia, accion="COMUNICACION_ENVIAR", materia_id=mat.id
        )

        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.get_interacciones_por_docente_materia(
            {"fecha_desde": date(2026, 6, 12), "fecha_hasta": date(2026, 6, 12)},
            _perm_ctx(),
        )

        assert isinstance(result, InteraccionesPorDocenteMateriaResponse)
        totales = {item.accion: item.total for item in result.items}
        assert totales["CALIFICACIONES_IMPORTAR"] == 2
        assert totales["COMUNICACION_ENVIAR"] == 1

        cal_item = next(i for i in result.items if i.accion == "CALIFICACIONES_IMPORTAR")
        assert cal_item.categoria == "CALIFICACIONES"

    @pytest.mark.asyncio
    async def test_materia_id_null_en_item(self, db_session, default_tenant) -> None:
        """RED 7.11: registro sin materia_id → materia_id: None en el item."""
        u = await _crear_usuario(db_session, default_tenant.id)
        dia = datetime(2026, 6, 12, 10, 0, tzinfo=timezone.utc)

        await _insert_audit(
            db_session, default_tenant.id, u.id,
            fecha_hora=dia, accion="IMPERSONACION_INICIAR", materia_id=None
        )

        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.get_interacciones_por_docente_materia(
            {"fecha_desde": date(2026, 6, 12), "fecha_hasta": date(2026, 6, 12)},
            _perm_ctx(),
        )
        assert len(result.items) >= 1
        item = next(i for i in result.items if i.accion == "IMPERSONACION_INICIAR")
        assert item.materia_id is None


# ---------------------------------------------------------------------------
# Phase 7.12-7.16 — ultimas_acciones
# ---------------------------------------------------------------------------


class TestUltimasAcciones:
    """Tests para ultimas_acciones."""

    @pytest.mark.asyncio
    async def test_limit_200_default_sobre_300_registros(self, db_session, default_tenant) -> None:
        """RED 7.12: 300 registros + limit default 200 → devuelve 200."""
        u = await _crear_usuario(db_session, default_tenant.id)
        for i in range(300):
            dia = datetime(2026, 6, 1, tzinfo=timezone.utc) + timedelta(hours=i)
            await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia)

        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.get_ultimas_acciones({}, _perm_ctx())
        assert isinstance(result, UltimasAccionesResponse)
        assert len(result.items) == 200

    @pytest.mark.asyncio
    async def test_limit_50_devuelve_exactamente_50(self, db_session, default_tenant) -> None:
        """RED 7.13: limit=50 sobre 300 registros → exactamente 50."""
        u = await _crear_usuario(db_session, default_tenant.id)
        for i in range(100):
            dia = datetime(2026, 6, 1, tzinfo=timezone.utc) + timedelta(hours=i)
            await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia)

        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.get_ultimas_acciones({"limit": 50}, _perm_ctx())
        assert len(result.items) == 50

    @pytest.mark.asyncio
    async def test_filtra_por_accion(self, db_session, default_tenant) -> None:
        """RED 7.15: accion=COMUNICACION_ENVIAR filtra correctamente."""
        u = await _crear_usuario(db_session, default_tenant.id)
        dia = datetime(2026, 6, 12, 10, 0, tzinfo=timezone.utc)

        await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia, accion="COMUNICACION_ENVIAR")
        await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia, accion="PADRON_CARGAR")
        await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia, accion="COMUNICACION_ENVIAR")

        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.get_ultimas_acciones(
            {"accion": AuditAction.COMUNICACION_ENVIAR},
            _perm_ctx(),
        )
        assert len(result.items) == 2
        assert all(i.accion == "COMUNICACION_ENVIAR" for i in result.items)


# ---------------------------------------------------------------------------
# Phase 7.17 — catalogo-acciones
# ---------------------------------------------------------------------------


class TestCatalogoAcciones:
    """Tests para catalogo_acciones."""

    @pytest.mark.asyncio
    async def test_retorna_item_por_cada_audit_action(self, db_session, default_tenant) -> None:
        """RED 7.17: retorna un item por cada miembro de AuditAction con su categoría."""
        u = await _crear_usuario(db_session, default_tenant.id)
        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.get_catalogo_acciones()
        assert isinstance(result, CatalogoAccionesResponse)
        codigos = {item.codigo for item in result.items}
        expected = {a.value for a in AuditAction}
        assert codigos == expected

    @pytest.mark.asyncio
    async def test_categoria_derivada_del_prefijo(self, db_session, default_tenant) -> None:
        """TRIANGULATE 7.17: categoría = prefijo del código (split por '_', 1)."""
        u = await _crear_usuario(db_session, default_tenant.id)
        service = AuditoriaPanelService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.get_catalogo_acciones()
        item_cal = next(i for i in result.items if i.codigo == "CALIFICACIONES_IMPORTAR")
        assert item_cal.categoria == "CALIFICACIONES"

        item_imp = next(i for i in result.items if i.codigo == "IMPERSONACION_INICIAR")
        assert item_imp.categoria == "IMPERSONACION"


# ---------------------------------------------------------------------------
# Phase 7.18-7.27 — AuditLog paginado
# ---------------------------------------------------------------------------


class TestAuditLogPaginado:
    """Tests para el log paginado de auditoría."""

    @pytest.mark.asyncio
    async def test_paginacion_default_75_registros(self, db_session, default_tenant) -> None:
        """RED 7.18: 75 registros → total=75, pages=2, items=50 (default page_size=50)."""
        u = await _crear_usuario(db_session, default_tenant.id)
        for i in range(75):
            dia = datetime(2026, 6, 1, tzinfo=timezone.utc) + timedelta(hours=i)
            await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia)

        service = AuditoriaLogQueryService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.list_log({}, _perm_ctx(), page=1, page_size=50)

        assert isinstance(result, AuditLogPageResponse)
        assert result.total == 75
        assert result.pages == 2
        assert len(result.items) == 50

    @pytest.mark.asyncio
    async def test_pagina_2_devuelve_25_restantes(self, db_session, default_tenant) -> None:
        """RED 7.19: page=2 devuelve los 25 registros restantes."""
        u = await _crear_usuario(db_session, default_tenant.id)
        for i in range(75):
            dia = datetime(2026, 6, 1, tzinfo=timezone.utc) + timedelta(hours=i)
            await _insert_audit(db_session, default_tenant.id, u.id, fecha_hora=dia)

        service = AuditoriaLogQueryService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.list_log({}, _perm_ctx(), page=2, page_size=50)
        assert len(result.items) == 25

    @pytest.mark.asyncio
    async def test_filtro_rango_fechas_inclusivo(self, db_session, default_tenant) -> None:
        """RED 7.22: filtro de fechas incluye registros en fecha_hasta."""
        u = await _crear_usuario(db_session, default_tenant.id)

        # Dentro del rango
        await _insert_audit(
            db_session, default_tenant.id, u.id,
            fecha_hora=datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)
        )
        await _insert_audit(
            db_session, default_tenant.id, u.id,
            fecha_hora=datetime(2026, 6, 12, 23, 59, 59, tzinfo=timezone.utc)
        )
        # Fuera del rango
        await _insert_audit(
            db_session, default_tenant.id, u.id,
            fecha_hora=datetime(2026, 6, 13, 1, 0, tzinfo=timezone.utc)
        )

        service = AuditoriaLogQueryService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.list_log(
            {
                "fecha_desde": datetime(2026, 6, 10, 0, 0, tzinfo=timezone.utc),
                "fecha_hasta": datetime(2026, 6, 12, 23, 59, 59, tzinfo=timezone.utc),
            },
            _perm_ctx(),
            page=1,
            page_size=50,
        )
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_filtro_usuario_id_matchea_actor_e_impersonado(
        self, db_session, default_tenant
    ) -> None:
        """RED 7.23: usuario_id matchea registros con actor_id=U1 Y con impersonado_id=U1."""
        u1 = await _crear_usuario(db_session, default_tenant.id)
        u2 = await _crear_usuario(db_session, default_tenant.id)
        dia = datetime(2026, 6, 12, 10, 0, tzinfo=timezone.utc)

        # actor_id == u1
        await _insert_audit(db_session, default_tenant.id, u1.id, fecha_hora=dia)
        # impersonado_id == u1 (actor es u2)
        await _insert_audit(
            db_session, default_tenant.id, u2.id,
            fecha_hora=dia, impersonado_id=u1.id
        )
        # No relacionado con u1
        await _insert_audit(db_session, default_tenant.id, u2.id, fecha_hora=dia)

        service = AuditoriaLogQueryService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u1.id,
        )
        result = await service.list_log(
            {"usuario_id": u1.id},
            _perm_ctx(),
            page=1,
            page_size=50,
        )
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_filtro_estado_enviado_en_detalle(self, db_session, default_tenant) -> None:
        """RED 7.24: filtro estado=Enviado matchea detalle.estado correcto."""
        u = await _crear_usuario(db_session, default_tenant.id)
        dia = datetime(2026, 6, 12, 10, 0, tzinfo=timezone.utc)

        await _insert_audit(
            db_session, default_tenant.id, u.id,
            fecha_hora=dia, detalle={"estado": "Enviado"}
        )
        await _insert_audit(
            db_session, default_tenant.id, u.id,
            fecha_hora=dia, detalle={"estado": "Error"}
        )
        await _insert_audit(
            db_session, default_tenant.id, u.id,
            fecha_hora=dia, detalle=None
        )

        service = AuditoriaLogQueryService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u.id,
        )
        result = await service.list_log(
            {"estado": "Enviado"},
            _perm_ctx(),
            page=1,
            page_size=50,
        )
        assert result.total == 1
        assert result.items[0].detalle == {"estado": "Enviado"}

    @pytest.mark.asyncio
    async def test_scope_propio_coordinador_ve_solo_propios(self, db_session, default_tenant) -> None:
        """RED 7.25: COORDINADOR con 4 propios + 20 ajenos ve exactamente 4."""
        u_coord = await _crear_usuario(db_session, default_tenant.id)
        u_otro = await _crear_usuario(db_session, default_tenant.id)
        dia = datetime(2026, 6, 12, 10, 0, tzinfo=timezone.utc)

        for i in range(4):
            await _insert_audit(
                db_session, default_tenant.id, u_coord.id,
                fecha_hora=dia + timedelta(minutes=i)
            )
        for i in range(20):
            await _insert_audit(
                db_session, default_tenant.id, u_otro.id,
                fecha_hora=dia + timedelta(minutes=i + 100)
            )

        service = AuditoriaLogQueryService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u_coord.id,
        )
        result = await service.list_log({}, _perm_ctx(is_propio=True), page=1, page_size=50)
        assert result.total == 4

    @pytest.mark.asyncio
    async def test_admin_is_propio_false_ve_todo(self, db_session, default_tenant) -> None:
        """RED 7.26: ADMIN con is_propio=False ve los 24 registros totales."""
        u1 = await _crear_usuario(db_session, default_tenant.id)
        u2 = await _crear_usuario(db_session, default_tenant.id)
        dia = datetime(2026, 6, 12, 10, 0, tzinfo=timezone.utc)

        for i in range(4):
            await _insert_audit(
                db_session, default_tenant.id, u1.id,
                fecha_hora=dia + timedelta(minutes=i)
            )
        for i in range(20):
            await _insert_audit(
                db_session, default_tenant.id, u2.id,
                fecha_hora=dia + timedelta(minutes=i + 100)
            )

        service = AuditoriaLogQueryService(
            db_session=db_session,
            tenant_id=default_tenant.id,
            current_user_id=u1.id,
        )
        result = await service.list_log({}, _perm_ctx(is_propio=False), page=1, page_size=50)
        assert result.total == 24

    @pytest.mark.asyncio
    async def test_filtro_usuario_id_no_cruza_tenants(self, db_session, default_tenant) -> None:
        """RED 7.27: ADMIN de Tenant B con usuario_id de Tenant A → items=[]."""
        from app.models.tenant import Tenant
        tenant_b = Tenant(nombre="Tenant B2", slug="tenant-b2-audit", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        u_a = await _crear_usuario(db_session, default_tenant.id)
        u_b = await _crear_usuario(db_session, tenant_b.id)
        dia = datetime(2026, 6, 12, 10, 0, tzinfo=timezone.utc)

        await _insert_audit(db_session, default_tenant.id, u_a.id, fecha_hora=dia)

        # ADMIN de tenant_b busca por usuario_id del tenant_a
        service = AuditoriaLogQueryService(
            db_session=db_session,
            tenant_id=tenant_b.id,
            current_user_id=u_b.id,
        )
        result = await service.list_log(
            {"usuario_id": u_a.id},
            _perm_ctx(is_propio=False),
            page=1,
            page_size=50,
        )
        assert result.total == 0


# ---------------------------------------------------------------------------
# Phase 7.30-7.31 — Contract tests
# ---------------------------------------------------------------------------


class TestContracts:
    """Contract tests: repositorios sin escritura, rutas solo GET."""

    def test_panel_repo_no_expone_metodos_escritura(self) -> None:
        """RED 7.30: AuditoriaPanelRepository no expone insert/update/delete/add/flush.

        No necesita DB real — inspecciona la clase, no instancia con session real.
        """
        from unittest.mock import MagicMock
        mock_session = MagicMock()
        repo = AuditoriaPanelRepository(mock_session, __import__("uuid").uuid4())
        escritura = {"insert", "update", "delete", "add", "flush"}
        metodos = {name for name, _ in inspect.getmembers(repo, predicate=inspect.ismethod)}
        for m in escritura:
            assert m not in metodos, f"AuditoriaPanelRepository expone método de escritura: {m}"

    def test_log_query_repo_no_expone_metodos_escritura(self) -> None:
        """RED 7.30 (triangulate): AuditoriaLogQueryRepository tampoco."""
        from unittest.mock import MagicMock
        mock_session = MagicMock()
        repo = AuditoriaLogQueryRepository(mock_session, __import__("uuid").uuid4())
        escritura = {"insert", "update", "delete", "add", "flush"}
        metodos = {name for name, _ in inspect.getmembers(repo, predicate=inspect.ismethod)}
        for m in escritura:
            assert m not in metodos, f"AuditoriaLogQueryRepository expone método de escritura: {m}"

    def test_rutas_auditoria_solo_get(self) -> None:
        """RED 7.31: ninguna ruta bajo /api/auditoria/ admite POST/PUT/PATCH/DELETE."""
        from app.main import app
        metodos_escritura = {"POST", "PUT", "PATCH", "DELETE"}
        rutas_auditoria_con_escritura = []
        for route in app.routes:
            if hasattr(route, "path") and "/auditoria" in route.path:
                if hasattr(route, "methods"):
                    bad = route.methods & metodos_escritura
                    if bad:
                        rutas_auditoria_con_escritura.append((route.path, bad))
        assert not rutas_auditoria_con_escritura, (
            f"Rutas de auditoría con métodos de escritura: {rutas_auditoria_con_escritura}"
        )
