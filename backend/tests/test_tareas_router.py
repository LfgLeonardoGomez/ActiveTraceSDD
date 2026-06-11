"""Tests de integración para router de tareas (C-16).

Strict TDD: RED → GREEN → TRIANGULATE.
Verifica endpoints protegidos por require_permission("tareas:gestionar").
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core import security
from app.models.user import Usuario
from app.repositories.rbac_repository import (
    RolRepository,
    PermisoRepository,
    RolPermisoRepository,
)


async def _create_user_with_role(
    db_session: AsyncSession,
    tenant_id,
    email: str,
    role_codes: list[str],
) -> tuple[Usuario, str]:
    """Helper: crea usuario y emite access token con roles específicos."""
    user = Usuario(
        nombre="Test",
        apellidos="User",
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
        roles=role_codes,
    )
    return user, token


async def _create_user_with_permission(
    db_session: AsyncSession, tenant_id, email: str
) -> str:
    """Crea usuario con rol ADMIN que tiene permiso tareas:gestionar."""
    rol_repo = RolRepository(db_session, tenant_id)
    perm_repo = PermisoRepository(db_session, tenant_id)
    rp_repo = RolPermisoRepository(db_session, tenant_id)

    admin_rol = await rol_repo.create(codigo="ADMIN", nombre="Administrador")
    perm = await perm_repo.create(codigo="tareas:gestionar", nombre="Gestionar tareas", modulo="tareas")
    await rp_repo.create(rol_id=admin_rol.id, permiso_id=perm.id, es_propio=False)

    _, token = await _create_user_with_role(db_session, tenant_id, email, ["ADMIN"])
    return token


async def _create_user_no_permission(
    db_session: AsyncSession, tenant_id, email: str
) -> str:
    """Crea usuario con rol NEXO sin permisos."""
    rol_repo = RolRepository(db_session, tenant_id)
    await rol_repo.create(codigo="NEXO", nombre="Nexo")

    _, token = await _create_user_with_role(db_session, tenant_id, email, ["NEXO"])
    return token


# ---------------------------------------------------------------------------
# Grupo 1: CRUD endpoints
# ---------------------------------------------------------------------------


class TestTareaRouterCRUD:
    """Task 6.1: endpoints CRUD."""

    @pytest.fixture
    async def admin_token(self, db_session: AsyncSession, default_tenant):
        return await _create_user_with_permission(db_session, default_tenant.id, "admin@test.com")

    @pytest.fixture
    async def no_perms_token(self, db_session: AsyncSession, default_tenant):
        return await _create_user_no_permission(db_session, default_tenant.id, "nexo@test.com")

    @pytest.mark.asyncio
    async def test_create_tarea(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """RED: POST /api/tareas/ crea tarea (201)."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        resp = await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "Nueva tarea", "asignado_a": str(assignee.id)},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["titulo"] == "Nueva tarea"
        assert data["estado"] == "Pendiente"

    @pytest.mark.asyncio
    async def test_list_tareas(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """GREEN: GET /api/tareas/ lista tareas."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc2@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "T1", "asignado_a": str(assignee.id)},
        )

        resp = await async_client.get(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_tarea(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """GREEN: GET /api/tareas/{id} devuelve tarea."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc3@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        create_resp = await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "Buscar", "asignado_a": str(assignee.id)},
        )
        tarea_id = create_resp.json()["id"]

        resp = await async_client.get(
            f"/api/tareas/{tarea_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == tarea_id

    @pytest.mark.asyncio
    async def test_update_tarea(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: PATCH /api/tareas/{id} actualiza."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc4@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        create_resp = await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "Original", "asignado_a": str(assignee.id)},
        )
        tarea_id = create_resp.json()["id"]

        resp = await async_client.patch(
            f"/api/tareas/{tarea_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "Actualizado"},
        )
        assert resp.status_code == 200
        assert resp.json()["titulo"] == "Actualizado"

    @pytest.mark.asyncio
    async def test_delete_tarea(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: DELETE /api/tareas/{id} soft delete."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc5@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        create_resp = await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "Eliminar", "asignado_a": str(assignee.id)},
        )
        tarea_id = create_resp.json()["id"]

        resp = await async_client.delete(
            f"/api/tareas/{tarea_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_no_permission_returns_403(self, async_client: AsyncClient, no_perms_token):
        """TRIANGULATE: sin permiso → 403."""
        resp = await async_client.get(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {no_perms_token}"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Grupo 2: State machine endpoints
# ---------------------------------------------------------------------------


class TestTareaRouterEstado:
    """Task 6.1: endpoints de estado."""

    @pytest.fixture
    async def admin_token(self, db_session: AsyncSession, default_tenant):
        return await _create_user_with_permission(db_session, default_tenant.id, "admin2@test.com")

    @pytest.mark.asyncio
    async def test_cambiar_estado(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """RED: PATCH /api/tareas/{id}/estado cambia estado."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc6@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        token_assignee = security.create_access_token(
            user_id=assignee.id, tenant_id=default_tenant.id, roles=["ADMIN"]
        )
        # Crear tarea como admin
        create_resp = await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "Tarea", "asignado_a": str(assignee.id)},
        )
        tarea_id = create_resp.json()["id"]

        resp = await async_client.patch(
            f"/api/tareas/{tarea_id}/estado",
            headers={"Authorization": f"Bearer {token_assignee}"},
            json={"estado": "En progreso"},
        )
        assert resp.status_code == 200
        assert resp.json()["estado"] == "En progreso"

    @pytest.mark.asyncio
    async def test_aprobar_tarea(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """GREEN: POST /api/tareas/{id}/aprobar."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc7@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        token_assignee = security.create_access_token(
            user_id=assignee.id, tenant_id=default_tenant.id, roles=["ADMIN"]
        )
        create_resp = await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "Tarea", "asignado_a": str(assignee.id)},
        )
        tarea_id = create_resp.json()["id"]

        # Avanzar a En progreso y Resuelta
        await async_client.patch(
            f"/api/tareas/{tarea_id}/estado",
            headers={"Authorization": f"Bearer {token_assignee}"},
            json={"estado": "En progreso"},
        )
        await async_client.patch(
            f"/api/tareas/{tarea_id}/estado",
            headers={"Authorization": f"Bearer {token_assignee}"},
            json={"estado": "Resuelta"},
        )

        resp = await async_client.post(
            f"/api/tareas/{tarea_id}/aprobar",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["aprobada"] is True

    @pytest.mark.asyncio
    async def test_devolver_tarea(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """GREEN: POST /api/tareas/{id}/devolver."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc8@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        token_assignee = security.create_access_token(
            user_id=assignee.id, tenant_id=default_tenant.id, roles=["ADMIN"]
        )
        create_resp = await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "Tarea", "asignado_a": str(assignee.id)},
        )
        tarea_id = create_resp.json()["id"]

        await async_client.patch(
            f"/api/tareas/{tarea_id}/estado",
            headers={"Authorization": f"Bearer {token_assignee}"},
            json={"estado": "En progreso"},
        )
        await async_client.patch(
            f"/api/tareas/{tarea_id}/estado",
            headers={"Authorization": f"Bearer {token_assignee}"},
            json={"estado": "Resuelta"},
        )

        resp = await async_client.post(
            f"/api/tareas/{tarea_id}/devolver",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"observacion": "Necesita rework"},
        )
        assert resp.status_code == 200
        assert resp.json()["estado"] == "En progreso"
        assert resp.json()["devuelta"] is True


# ---------------------------------------------------------------------------
# Grupo 3: Delegación y comentarios
# ---------------------------------------------------------------------------


class TestTareaRouterDelegacionComentarios:
    """Task 6.1: delegar y comentarios."""

    @pytest.fixture
    async def admin_token(self, db_session: AsyncSession, default_tenant):
        return await _create_user_with_permission(db_session, default_tenant.id, "admin3@test.com")

    @pytest.mark.asyncio
    async def test_delegar_tarea(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """RED: POST /api/tareas/{id}/delegar."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc9@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        nuevo = Usuario(
            nombre="Nuevo", apellidos="Doc", email="nuevo@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add_all([assignee, nuevo])
        await db_session.commit()
        await db_session.refresh(assignee)
        await db_session.refresh(nuevo)

        create_resp = await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "Tarea", "asignado_a": str(assignee.id)},
        )
        tarea_id = create_resp.json()["id"]

        resp = await async_client.post(
            f"/api/tareas/{tarea_id}/delegar",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"nuevo_asignado_id": str(nuevo.id)},
        )
        assert resp.status_code == 200
        assert resp.json()["asignado_a"] == str(nuevo.id)

    @pytest.mark.asyncio
    async def test_crear_comentario(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """GREEN: POST /api/tareas/{id}/comentarios."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc10@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        create_resp = await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "Tarea", "asignado_a": str(assignee.id)},
        )
        tarea_id = create_resp.json()["id"]

        resp = await async_client.post(
            f"/api/tareas/{tarea_id}/comentarios",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"contenido": "Comentario de prueba"},
        )
        assert resp.status_code == 201
        assert resp.json()["contenido"] == "Comentario de prueba"

    @pytest.mark.asyncio
    async def test_list_comentarios(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """GREEN: GET /api/tareas/{id}/comentarios."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc11@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        create_resp = await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "Tarea", "asignado_a": str(assignee.id)},
        )
        tarea_id = create_resp.json()["id"]

        await async_client.post(
            f"/api/tareas/{tarea_id}/comentarios",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"contenido": "C1"},
        )
        await async_client.post(
            f"/api/tareas/{tarea_id}/comentarios",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"contenido": "C2"},
        )

        resp = await async_client.get(
            f"/api/tareas/{tarea_id}/comentarios",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2


# ---------------------------------------------------------------------------
# Grupo 4: mis-tareas
# ---------------------------------------------------------------------------


class TestTareaRouterMisTareas:
    """Task 6.1: endpoint mis-tareas."""

    @pytest.fixture
    async def admin_token(self, db_session: AsyncSession, default_tenant):
        return await _create_user_with_permission(db_session, default_tenant.id, "admin4@test.com")

    @pytest.mark.asyncio
    async def test_mis_tareas(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """RED: GET /api/tareas/mis-tareas."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc12@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        token_assignee = security.create_access_token(
            user_id=assignee.id, tenant_id=default_tenant.id, roles=["ADMIN"]
        )
        await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "T1", "asignado_a": str(assignee.id)},
        )
        await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "T2", "asignado_a": str(assignee.id)},
        )

        resp = await async_client.get(
            "/api/tareas/mis-tareas",
            headers={"Authorization": f"Bearer {token_assignee}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert all(item["asignado_a"] == str(assignee.id) for item in data["items"])

    @pytest.mark.asyncio
    async def test_mis_tareas_filter_estado(self, async_client: AsyncClient, admin_token, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: filtro estado."""
        from app.models.user import Usuario
        assignee = Usuario(
            nombre="Doc", apellidos="Test", email="doc13@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(assignee)
        await db_session.commit()
        await db_session.refresh(assignee)

        token_assignee = security.create_access_token(
            user_id=assignee.id, tenant_id=default_tenant.id, roles=["ADMIN"]
        )
        await async_client.post(
            "/api/tareas/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"titulo": "T1", "asignado_a": str(assignee.id)},
        )

        resp = await async_client.get(
            "/api/tareas/mis-tareas?estado=Pendiente",
            headers={"Authorization": f"Bearer {token_assignee}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

        resp2 = await async_client.get(
            "/api/tareas/mis-tareas?estado=En progreso",
            headers={"Authorization": f"Bearer {token_assignee}"},
        )
        assert resp2.json()["total"] == 0
