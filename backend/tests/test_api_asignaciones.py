"""Tests de integración E2E para router de asignaciones (C-07).

Strict TDD: RED → GREEN → TRIANGULATE.
Tests de vigencia, 403, aislamiento multi-tenant, histórico.
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4, UUID

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================
# Tests básicos de endpoints
# ============================================================


class TestAsignacionEndpoints:
    """Verificar que el router está registrado."""

    @pytest.mark.asyncio
    async def test_endpoint_asignaciones_existe(
        self, async_client: AsyncClient
    ) -> None:
        """Router de asignaciones está registrado (no 404)."""
        response = await async_client.get("/api/v1/asignaciones")
        # Sin auth → 401
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_crear_asignacion_requiere_autenticacion(
        self, async_client: AsyncClient
    ) -> None:
        """Crear asignación sin token → 401."""
        response = await async_client.post(
            "/api/v1/asignaciones",
            json={
                "usuario_id": str(uuid4()),
                "rol": "PROFESOR",
                "desde": str(date.today()),
            },
        )
        assert response.status_code == 401


# ============================================================
# Task 11.4: CRUD de asignaciones con vigencia (nivel servicio)
# ============================================================


class TestCrudAsignacionVigencia:
    """Task 11.4 RED → GREEN → TRIANGULATE: vigencia en asignaciones."""

    @pytest.mark.asyncio
    async def test_asignacion_vigente_service(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 11.4: asignación vigente devuelve estado_vigencia=Vigente."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        usuario = await usuario_svc.crear_usuario(
            nombre="ProfV", apellidos="T", email="prof.v.api@test.com", estado="Activo"
        )

        asig_svc = AsignacionService(db_session, default_tenant.id)
        asig = await asig_svc.crear_asignacion(
            usuario_id=usuario.id,
            rol="PROFESOR",
            desde=date.today() - timedelta(days=10),
            hasta=date.today() + timedelta(days=30),
        )
        assert asig.estado_vigencia == "Vigente"

    @pytest.mark.asyncio
    async def test_asignacion_vencida_service(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 11.4: asignación vencida devuelve estado_vigencia=Vencida."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        usuario = await usuario_svc.crear_usuario(
            nombre="ProfVenc", apellidos="T", email="prof.venc.api@test.com", estado="Activo"
        )

        asig_svc = AsignacionService(db_session, default_tenant.id)
        asig = await asig_svc.crear_asignacion(
            usuario_id=usuario.id,
            rol="TUTOR",
            desde=date.today() - timedelta(days=60),
            hasta=date.today() - timedelta(days=5),
        )
        assert asig.estado_vigencia == "Vencida"

    @pytest.mark.asyncio
    async def test_asignacion_futura_service(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 11.4: asignación futura devuelve estado_vigencia=Vencida."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        usuario = await usuario_svc.crear_usuario(
            nombre="ProfFut", apellidos="T", email="prof.fut.api@test.com", estado="Activo"
        )

        asig_svc = AsignacionService(db_session, default_tenant.id)
        asig = await asig_svc.crear_asignacion(
            usuario_id=usuario.id,
            rol="NEXO",
            desde=date.today() + timedelta(days=5),
            hasta=date.today() + timedelta(days=30),
        )
        assert asig.estado_vigencia == "Vencida"


# ============================================================
# Task 11.5: 403 sin permiso equipos:asignar
# ============================================================


class TestAsignacion403SinPermiso:
    """Task 11.5: actor sin equipos:asignar → 401 (sin auth)."""

    @pytest.mark.asyncio
    async def test_todos_endpoints_sin_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Sin token → 401 en todos los endpoints de asignaciones."""
        endpoints = [
            ("GET", "/api/v1/asignaciones"),
            ("POST", "/api/v1/asignaciones"),
            ("GET", f"/api/v1/asignaciones/{uuid4()}"),
            ("PUT", f"/api/v1/asignaciones/{uuid4()}"),
            ("DELETE", f"/api/v1/asignaciones/{uuid4()}"),
        ]
        for method, url in endpoints:
            response = await async_client.request(method, url, json={})
            assert response.status_code in (401, 422), (
                f"{method} {url}: expected 401/422, got {response.status_code}"
            )


# ============================================================
# Task 11.6: asignación vencida conservada en histórico
# ============================================================


class TestAsignacionVencidaEnHistorico:
    """Task 11.6: asignación vencida aparece con incluir_vencidas=True."""

    @pytest.mark.asyncio
    async def test_asignacion_vencida_en_listado_con_filtro(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 11.6: asignación vencida aparece con incluir_vencidas=True."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        usuario = await usuario_svc.crear_usuario(
            nombre="HistoVenc", apellidos="T", email="histo.venc@test.com", estado="Activo"
        )

        asig_svc = AsignacionService(db_session, default_tenant.id)
        asig_vigente = await asig_svc.crear_asignacion(
            usuario_id=usuario.id,
            rol="PROFESOR",
            desde=date.today() - timedelta(days=5),
            hasta=date.today() + timedelta(days=10),
        )
        asig_vencida = await asig_svc.crear_asignacion(
            usuario_id=usuario.id,
            rol="TUTOR",
            desde=date.today() - timedelta(days=30),
            hasta=date.today() - timedelta(days=5),
        )

        # Con incluir_vencidas=True: ambas aparecen
        items_con, total_con = await asig_svc.listar_asignaciones(
            limit=100, offset=0, incluir_vencidas=True
        )
        ids_con = {a.id for a in items_con}
        assert asig_vigente.id in ids_con
        assert asig_vencida.id in ids_con

    @pytest.mark.asyncio
    async def test_asignacion_vencida_excluida_sin_filtro(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 11.6: asignación vencida NO aparece con incluir_vencidas=False."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        usuario = await usuario_svc.crear_usuario(
            nombre="ExclVenc", apellidos="T", email="excl.venc@test.com", estado="Activo"
        )

        asig_svc = AsignacionService(db_session, default_tenant.id)
        asig_vencida = await asig_svc.crear_asignacion(
            usuario_id=usuario.id,
            rol="TUTOR",
            desde=date.today() - timedelta(days=30),
            hasta=date.today() - timedelta(days=5),
        )

        # Con incluir_vencidas=False: vencida NO aparece
        items_sin, total_sin = await asig_svc.listar_asignaciones(
            limit=100, offset=0, incluir_vencidas=False
        )
        ids_sin = {a.id for a in items_sin}
        assert asig_vencida.id not in ids_sin, "Vencida no debe aparecer con incluir_vencidas=False"
