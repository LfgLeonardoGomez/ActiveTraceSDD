"""Tests TDD para C-06 — Routers de Cohorte y Materia (integración HTTP).

Task 6.4 RED/GREEN, 6.5 TRIANGULATE — router cohortes.
Task 6.6 RED/GREEN, 6.7 TRIANGULATE — router materias.
Task 7.1-7.2 RBAC — permiso estructura:gestionar en tests de endpoints.
Task 8.1 — aislamiento cross-tenant.
"""

import pytest
from datetime import date
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.models.user import Usuario
from app.repositories.rbac_repository import (
    PermisoRepository,
    RolPermisoRepository,
    RolRepository,
)


# ---------------------------------------------------------------
# Helper: crear usuario con rol ADMIN que tiene estructura:gestionar
# ---------------------------------------------------------------


async def _create_admin_with_estructura(
    db_session: AsyncSession,
    tenant_id,
    email: str,
) -> tuple[Usuario, str]:
    """Crea usuario ADMIN con permiso estructura:gestionar y devuelve (user, token)."""
    rol_repo = RolRepository(db_session, tenant_id)
    perm_repo = PermisoRepository(db_session, tenant_id)
    rp_repo = RolPermisoRepository(db_session, tenant_id)

    admin_rol = await rol_repo.create(codigo="ADMIN", nombre="Administrador")
    perm = await perm_repo.create(
        codigo="estructura:gestionar",
        nombre="Gestionar estructura",
        modulo="estructura",
    )
    await rp_repo.create(rol_id=admin_rol.id, permiso_id=perm.id, es_propio=False)

    user = Usuario(
        nombre="Admin",
        apellidos="Test",
        email=email,
        estado="activo",
        tenant_id=tenant_id,
        password_hash=security.hash_password("Pass1234"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = security.create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        roles=["ADMIN"],
    )
    return user, token


async def _create_user_no_perms(
    db_session: AsyncSession,
    tenant_id,
    email: str,
) -> str:
    """Crea usuario sin permisos y devuelve token."""
    rol_repo = RolRepository(db_session, tenant_id)
    await rol_repo.create(codigo="NEXO", nombre="Nexo")

    user = Usuario(
        nombre="Nexo",
        apellidos="Test",
        email=email,
        estado="activo",
        tenant_id=tenant_id,
        password_hash=security.hash_password("Pass1234"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = security.create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        roles=["NEXO"],
    )
    return token


# ---------------------------------------------------------------
# Task 6.1 RED: ruta POST /api/v1/admin/carreras existe
# ---------------------------------------------------------------


class TestCarreraRouterRED:
    """Task 6.1 RED: verificar existencia de ruta."""

    @pytest.mark.asyncio
    async def test_post_carreras_ruta_existe(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 6.1: POST /api/v1/admin/carreras devuelve algo distinto de 404."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "routecheck@test.com"
        )
        resp = await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "TEST", "nombre": "Test Carrera"},
        )
        assert resp.status_code != 404

    @pytest.mark.asyncio
    async def test_post_carreras_exitoso(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 6.2: POST /api/v1/admin/carreras crea carrera con 201."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "create_car@test.com"
        )
        resp = await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "ING", "nombre": "Ingeniería"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["codigo"] == "ING"
        assert data["estado"] == "Activa"

    @pytest.mark.asyncio
    async def test_sin_permiso_estructura_gestionar_403(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 6.3: sin permiso → 403."""
        token = await _create_user_no_perms(
            db_session, default_tenant.id, "noperm_car@test.com"
        )
        resp = await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "TST", "nombre": "Test"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_listado_paginado_filtro_estado(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 6.3: listado con filtro por estado."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "list_car@test.com"
        )
        # Crear carrera activa
        await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "ACT", "nombre": "Activa"},
        )
        resp = await async_client.get(
            "/api/v1/admin/carreras?estado=Activa",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_edicion_codigo_duplicado_409(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 6.3: edición con código duplicado → 409."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "dup_car@test.com"
        )
        r1 = await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "ORIG", "nombre": "Original"},
        )
        await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "DUP2", "nombre": "DupTarget"},
        )
        car_id = r1.json()["id"]
        resp = await async_client.put(
            f"/api/v1/admin/carreras/{car_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "DUP2"},
        )
        assert resp.status_code == 409


# ---------------------------------------------------------------
# Task 6.4 RED/GREEN + 6.5 TRIANGULATE: router cohortes
# ---------------------------------------------------------------


class TestCohorteRouter:
    """Task 6.4 y 6.5: router de cohortes."""

    @pytest.mark.asyncio
    async def test_crear_cohorte_con_carrera_inactiva_409(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 6.4: POST cohorte con carrera inactiva → 409."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "coh_inac@test.com"
        )
        # Crear carrera y desactivarla
        r_car = await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "INACCAR", "nombre": "Inactiva"},
        )
        car_id = r_car.json()["id"]
        await async_client.put(
            f"/api/v1/admin/carreras/{car_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"estado": "Inactiva"},
        )
        resp = await async_client.post(
            "/api/v1/admin/cohortes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "carrera_id": car_id,
                "nombre": "2024",
                "anio": 2024,
                "vig_desde": "2024-03-01",
            },
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_crear_cohorte_exitoso(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 6.4: POST cohorte con carrera activa → 201."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "coh_ok@test.com"
        )
        r_car = await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "ACTCAR", "nombre": "Activa"},
        )
        car_id = r_car.json()["id"]

        resp = await async_client.post(
            "/api/v1/admin/cohortes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "carrera_id": car_id,
                "nombre": "2024",
                "anio": 2024,
                "vig_desde": "2024-03-01",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "2024"
        assert data["carrera_id"] == car_id

    @pytest.mark.asyncio
    async def test_filtro_por_carrera_id(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 6.5: filtro por carrera_id en GET /cohortes."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "coh_filt@test.com"
        )
        r_car = await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "FILTCAR", "nombre": "Filtrar"},
        )
        car_id = r_car.json()["id"]
        await async_client.post(
            "/api/v1/admin/cohortes",
            headers={"Authorization": f"Bearer {token}"},
            json={"carrera_id": car_id, "nombre": "2024", "anio": 2024, "vig_desde": "2024-03-01"},
        )

        resp = await async_client.get(
            f"/api/v1/admin/cohortes?carrera_id={car_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_cohorte_otro_tenant_retorna_404(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 6.5: cohorte de otro tenant retorna 404."""
        _, token_a = await _create_admin_with_estructura(
            db_session, default_tenant.id, "coh_tenA@test.com"
        )
        r_car = await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"codigo": "TENCAR", "nombre": "Tenant A"},
        )
        car_id = r_car.json()["id"]
        r_coh = await async_client.post(
            "/api/v1/admin/cohortes",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"carrera_id": car_id, "nombre": "2024", "anio": 2024, "vig_desde": "2024-03-01"},
        )
        coh_id = r_coh.json()["id"]

        # Crear tenant B con su propio admin
        from app.models.tenant import Tenant
        tenant_b = Tenant(nombre="Tenant B", slug="tenant-b", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        _, token_b = await _create_admin_with_estructura(
            db_session, tenant_b.id, "coh_tenB@test.com"
        )

        resp = await async_client.get(
            f"/api/v1/admin/cohortes/{coh_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404
