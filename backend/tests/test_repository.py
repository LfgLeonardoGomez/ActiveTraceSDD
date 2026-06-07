"""Tests de TDD para BaseRepository y dominio — C-02 Task Groups 3 & 6."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.user import Usuario
from app.models.tenant import Tenant
from app.core.database import Base


class TestBaseRepositoryFailClosed:
    """RED/GREEN/TRIANGULATE para BaseRepository fail-closed."""

    @pytest.mark.asyncio
    async def test_repository_raises_without_tenant_id(self, db_session):
        """RED: instanciar sin tenant_id lanza ValueError."""
        with pytest.raises(ValueError) as exc_info:
            BaseRepository(db_session, Usuario, tenant_id=None)
        assert "tenant_id" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_repository_raises_with_empty_tenant_id(self, db_session):
        """TRIANGULATE: tenant_id vacío también lanza ValueError."""
        with pytest.raises(ValueError):
            BaseRepository(db_session, Usuario, tenant_id="")


class TestBaseRepositoryTenantIsolation:
    """RED/GREEN/TRIANGULATE para aislamiento multi-tenant."""

    @pytest.mark.asyncio
    async def test_list_returns_only_tenant_records(self, db_session):
        """RED: list() solo devuelve registros del tenant scope."""
        # Crear dos tenants
        tenant_a = Tenant(nombre="Tenant A", slug="tenant-a", activo=True)
        tenant_b = Tenant(nombre="Tenant B", slug="tenant-b", activo=True)
        db_session.add_all([tenant_a, tenant_b])
        await db_session.commit()
        await db_session.refresh(tenant_a)
        await db_session.refresh(tenant_b)

        # Crear usuarios en ambos tenants
        user_a = Usuario(
            tenant_id=tenant_a.id,
            nombre="User A",
            apellidos="Test",
            email="a@example.com",
            estado="activo",
        )
        user_b = Usuario(
            tenant_id=tenant_b.id,
            nombre="User B",
            apellidos="Test",
            email="b@example.com",
            estado="activo",
        )
        db_session.add_all([user_a, user_b])
        await db_session.commit()

        repo_a = BaseRepository(db_session, Usuario, tenant_id=tenant_a.id)
        results_a = await repo_a.list()
        assert len(results_a) == 1
        assert results_a[0].nombre == "User A"

        repo_b = BaseRepository(db_session, Usuario, tenant_id=tenant_b.id)
        results_b = await repo_b.list()
        assert len(results_b) == 1
        assert results_b[0].nombre == "User B"

    @pytest.mark.asyncio
    async def test_get_by_id_is_scoped_by_tenant(self, db_session):
        """TRIANGULATE: get_by_id no encuentra registro de otro tenant."""
        tenant_a = Tenant(nombre="Tenant A", slug="tenant-a-2", activo=True)
        tenant_b = Tenant(nombre="Tenant B", slug="tenant-b-2", activo=True)
        db_session.add_all([tenant_a, tenant_b])
        await db_session.commit()
        await db_session.refresh(tenant_a)
        await db_session.refresh(tenant_b)

        user_b = Usuario(
            tenant_id=tenant_b.id,
            nombre="User B",
            apellidos="Test",
            email="b2@example.com",
            estado="activo",
        )
        db_session.add(user_b)
        await db_session.commit()
        await db_session.refresh(user_b)

        repo_a = BaseRepository(db_session, Usuario, tenant_id=tenant_a.id)
        result = await repo_a.get_by_id(user_b.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_sets_tenant_id(self, db_session):
        """TRIANGULATE: create() asigna tenant_id al registro."""
        tenant = Tenant(nombre="Tenant", slug="tenant-create", activo=True)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        repo = BaseRepository(db_session, Usuario, tenant_id=tenant.id)
        user = await repo.create(
            nombre="New",
            apellidos="User",
            email="new@example.com",
            estado="activo",
        )
        assert user.tenant_id == tenant.id
        assert user.nombre == "New"


class TestBaseRepositorySoftDelete:
    """RED/GREEN/TRIANGULATE para soft delete."""

    @pytest.mark.asyncio
    async def test_delete_sets_deleted_at(self, db_session):
        """RED: delete() setea deleted_at y no borra físicamente."""
        tenant = Tenant(nombre="Tenant", slug="tenant-soft", activo=True)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        user = Usuario(
            tenant_id=tenant.id,
            nombre="ToDelete",
            apellidos="User",
            email="delete@example.com",
            estado="activo",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repo = BaseRepository(db_session, Usuario, tenant_id=tenant.id)
        deleted = await repo.delete(user.id)
        assert deleted is True

        await db_session.refresh(user)
        assert user.deleted_at is not None

    @pytest.mark.asyncio
    async def test_list_excludes_deleted(self, db_session):
        """GREEN: list() no incluye registros soft-deleted."""
        tenant = Tenant(nombre="Tenant", slug="tenant-soft-2", activo=True)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        user = Usuario(
            tenant_id=tenant.id,
            nombre="ToDelete",
            apellidos="User",
            email="delete2@example.com",
            estado="activo",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repo = BaseRepository(db_session, Usuario, tenant_id=tenant.id)
        await repo.delete(user.id)

        results = await repo.list()
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_with_deleted_includes_deleted(self, db_session):
        """TRIANGULATE: with_deleted() sí incluye registros eliminados."""
        tenant = Tenant(nombre="Tenant", slug="tenant-soft-3", activo=True)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        user = Usuario(
            tenant_id=tenant.id,
            nombre="ToDelete",
            apellidos="User",
            email="delete3@example.com",
            estado="activo",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repo = BaseRepository(db_session, Usuario, tenant_id=tenant.id)
        await repo.delete(user.id)

        results = await repo.with_deleted().list()
        assert len(results) == 1
        assert results[0].deleted_at is not None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_deleted(self, db_session):
        """TRIANGULATE: get_by_id no encuentra registros eliminados."""
        tenant = Tenant(nombre="Tenant", slug="tenant-soft-4", activo=True)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        user = Usuario(
            tenant_id=tenant.id,
            nombre="ToDelete",
            apellidos="User",
            email="delete4@example.com",
            estado="activo",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repo = BaseRepository(db_session, Usuario, tenant_id=tenant.id)
        await repo.delete(user.id)

        result = await repo.get_by_id(user.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_excludes_deleted(self, db_session):
        """TRIANGULATE: update no afecta registros eliminados."""
        tenant = Tenant(nombre="Tenant", slug="tenant-soft-5", activo=True)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        user = Usuario(
            tenant_id=tenant.id,
            nombre="Old",
            apellidos="User",
            email="old@example.com",
            estado="activo",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        repo = BaseRepository(db_session, Usuario, tenant_id=tenant.id)
        await repo.delete(user.id)

        updated = await repo.update(user.id, {"nombre": "New"})
        assert updated is None


class TestBaseRepositoryTimestamps:
    """RED/GREEN para timestamps automáticos."""

    @pytest.mark.asyncio
    async def test_create_sets_timestamps(self, db_session):
        """RED: create() setea created_at y updated_at."""
        tenant = Tenant(nombre="Tenant", slug="tenant-ts", activo=True)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        repo = BaseRepository(db_session, Usuario, tenant_id=tenant.id)
        user = await repo.create(
            nombre="Timestamp",
            apellidos="Test",
            email="ts@example.com",
            estado="activo",
        )
        assert user.created_at is not None
        assert user.updated_at is not None
        # Pueden diferir por microsegundos; validamos proximidad
        assert abs((user.created_at - user.updated_at).total_seconds()) < 1.0

    @pytest.mark.asyncio
    async def test_update_changes_updated_at(self, db_session):
        """GREEN: update() cambia updated_at."""
        import asyncio

        tenant = Tenant(nombre="Tenant", slug="tenant-ts-2", activo=True)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        repo = BaseRepository(db_session, Usuario, tenant_id=tenant.id)
        user = await repo.create(
            nombre="Before",
            apellidos="Test",
            email="before@example.com",
            estado="activo",
        )
        original = user.updated_at
        await asyncio.sleep(0.01)

        updated = await repo.update(user.id, {"nombre": "After"})
        assert updated is not None
        assert updated.updated_at > original

    @pytest.mark.asyncio
    async def test_no_hard_delete_in_repository(self, db_session):
        """TRIANGULATE: verificar que delete() no usa session.delete()."""
        tenant = Tenant(nombre="Tenant", slug="tenant-no-hard", activo=True)
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        repo = BaseRepository(db_session, Usuario, tenant_id=tenant.id)
        # Inspeccionar que no hay método que use session.delete
        import inspect
        source = inspect.getsource(repo.delete)
        assert "session.delete" not in source
