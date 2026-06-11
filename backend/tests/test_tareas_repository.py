"""Tests TDD para TareaRepository y ComentarioTareaRepository (C-16).

Strict TDD: RED → GREEN → TRIANGULATE.
Tests usan DB real (sin mocks — regla dura).
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _crear_usuario(db_session: AsyncSession, tenant_id, email: str = "doc@test.com"):
    from app.models.user import Usuario
    u = Usuario(
        tenant_id=tenant_id,
        nombre="Docente",
        apellidos="Test",
        email=email,
        estado="activo",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _crear_materia(db_session: AsyncSession, tenant_id, codigo: str = "MAT-01"):
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


async def _crear_tarea(
    db_session: AsyncSession,
    tenant_id,
    titulo: str,
    asignado_a,
    asignado_por,
    estado=None,
    materia_id=None,
):
    from app.models.tarea import Tarea, EstadoTarea
    t = Tarea(
        tenant_id=tenant_id,
        titulo=titulo,
        asignado_a=asignado_a,
        asignado_por=asignado_por,
        estado=estado or EstadoTarea.PENDIENTE,
        materia_id=materia_id,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


# ---------------------------------------------------------------------------
# Grupo 1: CRUD Tarea
# ---------------------------------------------------------------------------


class TestTareaRepositoryCRUD:
    """Task 4.1: CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_tarea(self, db_session: AsyncSession, default_tenant):
        """RED: create tarea → persiste."""
        from app.repositories.tarea_repository import TareaRepository
        from app.models.tarea import EstadoTarea

        assignee = await _crear_usuario(db_session, default_tenant.id, "a1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "a2@test.com")

        repo = TareaRepository(db_session, default_tenant.id)
        tarea = await repo.create({
            "titulo": "Nueva tarea",
            "descripcion": "Desc",
            "asignado_a": assignee.id,
            "asignado_por": assigner.id,
        })

        assert tarea.id is not None
        assert tarea.titulo == "Nueva tarea"
        assert tarea.estado == EstadoTarea.PENDIENTE
        assert tarea.tenant_id == default_tenant.id

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession, default_tenant):
        """GREEN: get_by_id devuelve la tarea."""
        from app.repositories.tarea_repository import TareaRepository

        assignee = await _crear_usuario(db_session, default_tenant.id, "b1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "b2@test.com")
        repo = TareaRepository(db_session, default_tenant.id)
        tarea = await repo.create({
            "titulo": "Buscar",
            "asignado_a": assignee.id,
            "asignado_por": assigner.id,
        })

        found = await repo.get_by_id(tarea.id)
        assert found is not None
        assert found.id == tarea.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: get_by_id devuelve None para ID inexistente."""
        from app.repositories.tarea_repository import TareaRepository

        repo = TareaRepository(db_session, default_tenant.id)
        found = await repo.get_by_id(uuid4())
        assert found is None

    @pytest.mark.asyncio
    async def test_update_tarea(self, db_session: AsyncSession, default_tenant):
        """GREEN: update modifica campos."""
        from app.repositories.tarea_repository import TareaRepository

        assignee = await _crear_usuario(db_session, default_tenant.id, "c1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "c2@test.com")
        repo = TareaRepository(db_session, default_tenant.id)
        tarea = await repo.create({
            "titulo": "Original",
            "asignado_a": assignee.id,
            "asignado_por": assigner.id,
        })

        updated = await repo.update(tarea.id, {"titulo": "Actualizado"})
        assert updated is not None
        assert updated.titulo == "Actualizado"

    @pytest.mark.asyncio
    async def test_soft_delete_tarea(self, db_session: AsyncSession, default_tenant):
        """GREEN: soft_delete setea deleted_at."""
        from app.repositories.tarea_repository import TareaRepository

        assignee = await _crear_usuario(db_session, default_tenant.id, "d1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "d2@test.com")
        repo = TareaRepository(db_session, default_tenant.id)
        tarea = await repo.create({
            "titulo": "Eliminar",
            "asignado_a": assignee.id,
            "asignado_por": assigner.id,
        })

        deleted = await repo.soft_delete(tarea.id)
        assert deleted is not None
        assert deleted.deleted_at is not None

        found = await repo.get_by_id(tarea.id)
        assert found is None


# ---------------------------------------------------------------------------
# Grupo 2: Listado y filtros
# ---------------------------------------------------------------------------


class TestTareaRepositoryList:
    """Task 4.1: listado con filtros y paginación."""

    @pytest.mark.asyncio
    async def test_list_por_tenant(self, db_session: AsyncSession, default_tenant):
        """RED: list_por_tenant devuelve tareas del tenant."""
        from app.repositories.tarea_repository import TareaRepository
        from app.models.tarea import EstadoTarea

        assignee = await _crear_usuario(db_session, default_tenant.id, "e1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "e2@test.com")
        repo = TareaRepository(db_session, default_tenant.id)
        await repo.create({"titulo": "T1", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await repo.create({"titulo": "T2", "asignado_a": assignee.id, "asignado_por": assigner.id})

        items, total = await repo.list_por_tenant(page=1, page_size=10)
        assert total == 2
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_list_por_tenant_filter_estado(self, db_session: AsyncSession, default_tenant):
        """GREEN: filtro por estado."""
        from app.repositories.tarea_repository import TareaRepository
        from app.models.tarea import EstadoTarea

        assignee = await _crear_usuario(db_session, default_tenant.id, "f1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "f2@test.com")
        repo = TareaRepository(db_session, default_tenant.id)
        t1 = await repo.create({"titulo": "T1", "asignado_a": assignee.id, "asignado_por": assigner.id, "estado": EstadoTarea.PENDIENTE})
        await repo.create({"titulo": "T2", "asignado_a": assignee.id, "asignado_por": assigner.id, "estado": EstadoTarea.EN_PROGRESO})

        items, total = await repo.list_por_tenant(page=1, page_size=10, estado=EstadoTarea.PENDIENTE)
        assert total == 1
        assert items[0].id == t1.id

    @pytest.mark.asyncio
    async def test_list_por_tenant_filter_asignado_a(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: filtro por asignado_a."""
        from app.repositories.tarea_repository import TareaRepository

        a1 = await _crear_usuario(db_session, default_tenant.id, "g1@test.com")
        a2 = await _crear_usuario(db_session, default_tenant.id, "g2@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "g3@test.com")
        repo = TareaRepository(db_session, default_tenant.id)
        t1 = await repo.create({"titulo": "T1", "asignado_a": a1.id, "asignado_por": assigner.id})
        await repo.create({"titulo": "T2", "asignado_a": a2.id, "asignado_por": assigner.id})

        items, total = await repo.list_por_tenant(page=1, page_size=10, asignado_a=a1.id)
        assert total == 1
        assert items[0].id == t1.id

    @pytest.mark.asyncio
    async def test_list_por_tenant_filter_materia(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: filtro por materia_id."""
        from app.repositories.tarea_repository import TareaRepository

        assignee = await _crear_usuario(db_session, default_tenant.id, "h1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "h2@test.com")
        materia = await _crear_materia(db_session, default_tenant.id, "MAT-FILTRO")
        repo = TareaRepository(db_session, default_tenant.id)
        t1 = await repo.create({"titulo": "T1", "asignado_a": assignee.id, "asignado_por": assigner.id, "materia_id": materia.id})
        await repo.create({"titulo": "T2", "asignado_a": assignee.id, "asignado_por": assigner.id})

        items, total = await repo.list_por_tenant(page=1, page_size=10, materia_id=materia.id)
        assert total == 1
        assert items[0].id == t1.id

    @pytest.mark.asyncio
    async def test_list_por_tenant_search(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: búsqueda por texto."""
        from app.repositories.tarea_repository import TareaRepository

        assignee = await _crear_usuario(db_session, default_tenant.id, "i1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "i2@test.com")
        repo = TareaRepository(db_session, default_tenant.id)
        t1 = await repo.create({"titulo": "Tarea especial", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await repo.create({"titulo": "Otra cosa", "asignado_a": assignee.id, "asignado_por": assigner.id})

        items, total = await repo.list_por_tenant(page=1, page_size=10, search="especial")
        assert total == 1
        assert items[0].id == t1.id

    @pytest.mark.asyncio
    async def test_list_por_tenant_pagination(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: paginación limita resultados."""
        from app.repositories.tarea_repository import TareaRepository

        assignee = await _crear_usuario(db_session, default_tenant.id, "j1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "j2@test.com")
        repo = TareaRepository(db_session, default_tenant.id)
        for i in range(5):
            await repo.create({"titulo": f"T{i}", "asignado_a": assignee.id, "asignado_por": assigner.id})

        items, total = await repo.list_por_tenant(page=1, page_size=2)
        assert total == 5
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_list_por_asignado(self, db_session: AsyncSession, default_tenant):
        """GREEN: list_por_asignado filtra por asignado_a."""
        from app.repositories.tarea_repository import TareaRepository
        from app.models.tarea import EstadoTarea

        a1 = await _crear_usuario(db_session, default_tenant.id, "k1@test.com")
        a2 = await _crear_usuario(db_session, default_tenant.id, "k2@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "k3@test.com")
        repo = TareaRepository(db_session, default_tenant.id)
        t1 = await repo.create({"titulo": "T1", "asignado_a": a1.id, "asignado_por": assigner.id, "estado": EstadoTarea.PENDIENTE})
        await repo.create({"titulo": "T2", "asignado_a": a2.id, "asignado_por": assigner.id, "estado": EstadoTarea.EN_PROGRESO})

        items, total = await repo.list_por_asignado(a1.id, page=1, page_size=10)
        assert total == 1
        assert items[0].id == t1.id

    @pytest.mark.asyncio
    async def test_list_por_asignado_filter_estado(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: list_por_asignado con filtro de estado."""
        from app.repositories.tarea_repository import TareaRepository
        from app.models.tarea import EstadoTarea

        a1 = await _crear_usuario(db_session, default_tenant.id, "l1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "l2@test.com")
        repo = TareaRepository(db_session, default_tenant.id)
        await repo.create({"titulo": "T1", "asignado_a": a1.id, "asignado_por": assigner.id, "estado": EstadoTarea.PENDIENTE})
        t2 = await repo.create({"titulo": "T2", "asignado_a": a1.id, "asignado_por": assigner.id, "estado": EstadoTarea.EN_PROGRESO})

        items, total = await repo.list_por_asignado(a1.id, page=1, page_size=10, estado=EstadoTarea.EN_PROGRESO)
        assert total == 1
        assert items[0].id == t2.id


# ---------------------------------------------------------------------------
# Grupo 3: Tenant isolation
# ---------------------------------------------------------------------------


class TestTareaRepositoryTenantIsolation:
    """Task 4.1: tenant isolation."""

    @pytest.mark.asyncio
    async def test_no_cross_tenant_access(self, db_session: AsyncSession, default_tenant):
        """RED: repo de tenant A no ve tareas de tenant B."""
        from app.models.tenant import Tenant
        from app.repositories.tarea_repository import TareaRepository

        tenant_b = Tenant(nombre="Tenant B", slug="tenant-b", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        assignee = await _crear_usuario(db_session, default_tenant.id, "m1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "m2@test.com")
        repo_a = TareaRepository(db_session, default_tenant.id)
        tarea = await repo_a.create({"titulo": "T A", "asignado_a": assignee.id, "asignado_por": assigner.id})

        repo_b = TareaRepository(db_session, tenant_b.id)
        found = await repo_b.get_by_id(tarea.id)
        assert found is None

        items, total = await repo_b.list_por_tenant(page=1, page_size=10)
        assert total == 0


# ---------------------------------------------------------------------------
# Grupo 4: ComentarioTareaRepository
# ---------------------------------------------------------------------------


class TestComentarioTareaRepository:
    """Task 4.2: CRUD de comentarios."""

    @pytest.mark.asyncio
    async def test_create_comentario(self, db_session: AsyncSession, default_tenant):
        """RED: create comentario → persiste."""
        from app.repositories.tarea_repository import ComentarioTareaRepository
        from app.models.tarea import Tarea

        assignee = await _crear_usuario(db_session, default_tenant.id, "n1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "n2@test.com")
        autor = await _crear_usuario(db_session, default_tenant.id, "n3@test.com")
        tarea = Tarea(
            tenant_id=default_tenant.id,
            titulo="Tarea",
            asignado_a=assignee.id,
            asignado_por=assigner.id,
        )
        db_session.add(tarea)
        await db_session.commit()
        await db_session.refresh(tarea)

        repo = ComentarioTareaRepository(db_session, default_tenant.id)
        comentario = await repo.create({
            "tarea_id": tarea.id,
            "autor_id": autor.id,
            "contenido": "Comentario",
        })
        assert comentario.id is not None
        assert comentario.tarea_id == tarea.id
        assert comentario.contenido == "Comentario"

    @pytest.mark.asyncio
    async def test_list_por_tarea_ordered(self, db_session: AsyncSession, default_tenant):
        """GREEN: list_por_tarea ordenado por created_at ASC."""
        from app.repositories.tarea_repository import ComentarioTareaRepository
        from app.models.tarea import Tarea

        assignee = await _crear_usuario(db_session, default_tenant.id, "o1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "o2@test.com")
        autor = await _crear_usuario(db_session, default_tenant.id, "o3@test.com")
        tarea = Tarea(
            tenant_id=default_tenant.id,
            titulo="Tarea",
            asignado_a=assignee.id,
            asignado_por=assigner.id,
        )
        db_session.add(tarea)
        await db_session.commit()
        await db_session.refresh(tarea)

        repo = ComentarioTareaRepository(db_session, default_tenant.id)
        c1 = await repo.create({"tarea_id": tarea.id, "autor_id": autor.id, "contenido": "Primero"})
        c2 = await repo.create({"tarea_id": tarea.id, "autor_id": autor.id, "contenido": "Segundo"})

        items, total = await repo.list_por_tarea(tarea.id, page=1, page_size=10)
        assert total == 2
        assert items[0].id == c1.id
        assert items[1].id == c2.id

    @pytest.mark.asyncio
    async def test_soft_delete_comentario(self, db_session: AsyncSession, default_tenant):
        """GREEN: soft_delete comentario."""
        from app.repositories.tarea_repository import ComentarioTareaRepository
        from app.models.tarea import Tarea

        assignee = await _crear_usuario(db_session, default_tenant.id, "p1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "p2@test.com")
        autor = await _crear_usuario(db_session, default_tenant.id, "p3@test.com")
        tarea = Tarea(
            tenant_id=default_tenant.id,
            titulo="Tarea",
            asignado_a=assignee.id,
            asignado_por=assigner.id,
        )
        db_session.add(tarea)
        await db_session.commit()
        await db_session.refresh(tarea)

        repo = ComentarioTareaRepository(db_session, default_tenant.id)
        comentario = await repo.create({"tarea_id": tarea.id, "autor_id": autor.id, "contenido": "Borrar"})

        deleted = await repo.soft_delete(comentario.id)
        assert deleted is not None
        assert deleted.deleted_at is not None

        items, total = await repo.list_por_tarea(tarea.id, page=1, page_size=10)
        assert total == 0
