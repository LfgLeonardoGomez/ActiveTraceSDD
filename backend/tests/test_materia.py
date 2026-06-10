"""Tests TDD para C-06 — Router de Materia y tests de integración transversales.

Task 6.6 RED/GREEN, 6.7 TRIANGULATE — router materias.
Task 8.1 — aislamiento cross-tenant completo.
Task 8.2 — flujo completo ciclo de vida carrera.
"""

import pytest
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


async def _create_admin_with_estructura(
    db_session: AsyncSession,
    tenant_id,
    email: str,
) -> tuple[Usuario, str]:
    """Crea usuario ADMIN con permiso estructura:gestionar."""
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


# ---------------------------------------------------------------
# Task 6.6 RED/GREEN: router materias
# ---------------------------------------------------------------


class TestMateriaRouter:
    """Task 6.6 y 6.7: router de materias."""

    @pytest.mark.asyncio
    async def test_post_materia_campo_extra_422(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 6.6: POST materia con campo extra → 422."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "mat_extra@test.com"
        )
        resp = await async_client.post(
            "/api/v1/admin/materias",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "MAT", "nombre": "Matemática", "campo_extra": "x"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_post_materia_exitoso(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 6.6: POST materia válida → 201."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "mat_ok@test.com"
        )
        resp = await async_client.post(
            "/api/v1/admin/materias",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "MAT101", "nombre": "Matemática I"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["codigo"] == "MAT101"
        assert data["estado"] == "Activa"

    @pytest.mark.asyncio
    async def test_codigo_duplicado_409(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 6.7: código duplicado → 409."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "mat_dup@test.com"
        )
        await async_client.post(
            "/api/v1/admin/materias",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "DUPMAT", "nombre": "Dup 1"},
        )
        resp = await async_client.post(
            "/api/v1/admin/materias",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "DUPMAT", "nombre": "Dup 2"},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_soft_delete_luego_no_encontrado(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 6.7: soft delete → 204; GET posterior → 404."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "mat_del@test.com"
        )
        r = await async_client.post(
            "/api/v1/admin/materias",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "DELMTX", "nombre": "A Borrar"},
        )
        mat_id = r.json()["id"]

        del_resp = await async_client.delete(
            f"/api/v1/admin/materias/{mat_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_resp.status_code == 204

        get_resp = await async_client.get(
            f"/api/v1/admin/materias/{mat_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 404


# ---------------------------------------------------------------
# Task 8.1: aislamiento cross-tenant completo
# ---------------------------------------------------------------


class TestCrossTenantIsolation:
    """Task 8.1: tenant B no ve recursos del tenant A."""

    @pytest.mark.asyncio
    async def test_cross_tenant_isolation_complete(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """8.1: carrera + cohorte + materia del tenant A invisibles para tenant B."""
        # Tenant A: crear recursos
        _, token_a = await _create_admin_with_estructura(
            db_session, default_tenant.id, "xten_a@test.com"
        )
        r_car = await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"codigo": "XTENCAR", "nombre": "Cross Tenant Carrera"},
        )
        car_id = r_car.json()["id"]

        await async_client.post(
            "/api/v1/admin/cohortes",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"carrera_id": car_id, "nombre": "2024", "anio": 2024, "vig_desde": "2024-03-01"},
        )
        await async_client.post(
            "/api/v1/admin/materias",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"codigo": "XTENMAT", "nombre": "Cross Tenant Materia"},
        )

        # Tenant B: no debe ver recursos del tenant A
        from app.models.tenant import Tenant
        tenant_b = Tenant(nombre="Tenant B Isolation", slug="ten-b-iso", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        _, token_b = await _create_admin_with_estructura(
            db_session, tenant_b.id, "xten_b@test.com"
        )

        for endpoint in ("/api/v1/admin/carreras", "/api/v1/admin/cohortes", "/api/v1/admin/materias"):
            resp = await async_client.get(
                endpoint,
                headers={"Authorization": f"Bearer {token_b}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 0, f"Tenant B vio datos del Tenant A en {endpoint}"


# ---------------------------------------------------------------
# Task 8.2: flujo completo ciclo de vida carrera
# ---------------------------------------------------------------


class TestCarreraLifecycle:
    """Task 8.2: flujo completo crear → editar → desactivar → eliminar."""

    @pytest.mark.asyncio
    async def test_carrera_full_lifecycle(
        self, async_client: AsyncClient, db_session: AsyncSession, default_tenant
    ) -> None:
        """8.2: flujo completo de ciclo de vida de carrera."""
        _, token = await _create_admin_with_estructura(
            db_session, default_tenant.id, "lifecycle@test.com"
        )

        # 1. Crear carrera
        r_create = await async_client.post(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
            json={"codigo": "LCYCLE", "nombre": "Lifecycle Carrera"},
        )
        assert r_create.status_code == 201
        car_id = r_create.json()["id"]

        # 2. Listar - debe aparecer
        r_list = await async_client.get(
            "/api/v1/admin/carreras",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert any(c["id"] == car_id for c in r_list.json()["items"])

        # 3. Editar nombre
        r_edit = await async_client.put(
            f"/api/v1/admin/carreras/{car_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"nombre": "Lifecycle Carrera Editada"},
        )
        assert r_edit.status_code == 200
        assert r_edit.json()["nombre"] == "Lifecycle Carrera Editada"

        # 4. Crear cohorte activa bajo la carrera
        r_coh = await async_client.post(
            "/api/v1/admin/cohortes",
            headers={"Authorization": f"Bearer {token}"},
            json={"carrera_id": car_id, "nombre": "2024", "anio": 2024, "vig_desde": "2024-03-01"},
        )
        assert r_coh.status_code == 201
        coh_id = r_coh.json()["id"]

        # 5. Desactivar carrera con cohorte activa → 409
        r_deact_fail = await async_client.put(
            f"/api/v1/admin/carreras/{car_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"estado": "Inactiva"},
        )
        assert r_deact_fail.status_code == 409

        # 6. Desactivar cohorte primero
        r_coh_deact = await async_client.put(
            f"/api/v1/admin/cohortes/{coh_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"estado": "Inactiva"},
        )
        assert r_coh_deact.status_code == 200

        # 7. Ahora desactivar carrera → OK
        r_deact_ok = await async_client.put(
            f"/api/v1/admin/carreras/{car_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"estado": "Inactiva"},
        )
        assert r_deact_ok.status_code == 200
        assert r_deact_ok.json()["estado"] == "Inactiva"

        # 8. Eliminar carrera (soft delete)
        r_del = await async_client.delete(
            f"/api/v1/admin/carreras/{car_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_del.status_code == 204

        # 9. GET posterior → 404
        r_get = await async_client.get(
            f"/api/v1/admin/carreras/{car_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_get.status_code == 404
