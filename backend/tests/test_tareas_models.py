"""Tests TDD para modelos y migración de tareas (C-16).

Strict TDD: RED → GREEN → TRIANGULATE.
Tests usan DB real (sin mocks — regla dura).
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _crear_usuario(db_session: AsyncSession, tenant_id, email: str = "doc@test.com"):
    """Crea un usuario mínimo para los tests."""
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


# ---------------------------------------------------------------------------
# Grupo 1: Enum EstadoTarea
# ---------------------------------------------------------------------------


class TestEstadoTareaEnum:
    """Task 2.1: validación de enum EstadoTarea."""

    def test_estado_tarea_valores(self) -> None:
        """RED: EstadoTarea tiene 4 valores."""
        from app.models.tarea import EstadoTarea

        assert EstadoTarea.PENDIENTE == "Pendiente"
        assert EstadoTarea.EN_PROGRESO == "En progreso"
        assert EstadoTarea.RESUELTA == "Resuelta"
        assert EstadoTarea.CANCELADA == "Cancelada"

    def test_estado_tarea_desde_string_valido(self) -> None:
        """GREEN: EstadoTarea se puede instanciar desde string."""
        from app.models.tarea import EstadoTarea

        assert EstadoTarea("Pendiente") == EstadoTarea.PENDIENTE
        assert EstadoTarea("En progreso") == EstadoTarea.EN_PROGRESO

    def test_estado_tarea_desde_string_invalido(self) -> None:
        """RED: EstadoTarea rechaza string inválido."""
        from app.models.tarea import EstadoTarea

        with pytest.raises(ValueError):
            EstadoTarea("Invalido")


# ---------------------------------------------------------------------------
# Grupo 2: Tarea model
# ---------------------------------------------------------------------------


class TestTareaModel:
    """Task 2.1: creación y defaults de Tarea."""

    @pytest.mark.asyncio
    async def test_crear_tarea_defaults(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED: crear Tarea → persiste con defaults correctos."""
        from app.models.tarea import Tarea, EstadoTarea

        assignee = await _crear_usuario(db_session, default_tenant.id, "assignee@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "assigner@test.com")
        materia = await _crear_materia(db_session, default_tenant.id)

        tarea = Tarea(
            tenant_id=default_tenant.id,
            titulo="Tarea de prueba",
            descripcion="Descripción",
            criterio_cierre="Criterio",
            asignado_a=assignee.id,
            asignado_por=assigner.id,
            materia_id=materia.id,
        )
        db_session.add(tarea)
        await db_session.commit()
        await db_session.refresh(tarea)

        assert tarea.id is not None
        assert tarea.tenant_id == default_tenant.id
        assert tarea.titulo == "Tarea de prueba"
        assert tarea.descripcion == "Descripción"
        assert tarea.criterio_cierre == "Criterio"
        assert tarea.estado == EstadoTarea.PENDIENTE
        assert tarea.aprobada is False
        assert tarea.devuelta is False
        assert tarea.asignado_a == assignee.id
        assert tarea.asignado_por == assigner.id
        assert tarea.revisada_por is None
        assert tarea.revisada_at is None
        assert tarea.materia_id == materia.id
        assert tarea.created_at is not None
        assert tarea.updated_at is not None
        assert tarea.deleted_at is None

    @pytest.mark.asyncio
    async def test_tarea_soft_delete(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN: soft delete setea deleted_at."""
        from app.models.tarea import Tarea

        assignee = await _crear_usuario(db_session, default_tenant.id, "s1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "s2@test.com")

        tarea = Tarea(
            tenant_id=default_tenant.id,
            titulo="Para eliminar",
            asignado_a=assignee.id,
            asignado_por=assigner.id,
        )
        db_session.add(tarea)
        await db_session.commit()
        await db_session.refresh(tarea)

        tarea.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(tarea)

        assert tarea.deleted_at is not None

    @pytest.mark.asyncio
    async def test_tarea_contexto_id_opaque(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: contexto_id acepta cualquier UUID sin FK."""
        from app.models.tarea import Tarea

        assignee = await _crear_usuario(db_session, default_tenant.id, "ctx@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "ctx2@test.com")
        ctx_id = uuid4()

        tarea = Tarea(
            tenant_id=default_tenant.id,
            titulo="Con contexto",
            asignado_a=assignee.id,
            asignado_por=assigner.id,
            contexto_id=ctx_id,
        )
        db_session.add(tarea)
        await db_session.commit()
        await db_session.refresh(tarea)

        assert tarea.contexto_id == ctx_id

    @pytest.mark.asyncio
    async def test_tarea_indexes_exist(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: índices definidos en el modelo existen en la tabla."""
        result = await db_session.execute(
            text(
                """
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'tarea'
                AND schemaname = 'public'
                """
            )
        )
        indexes = {row[0] for row in result.all()}
        assert "ix_tarea_tenant_estado" in indexes
        assert "ix_tarea_asignado_estado" in indexes
        assert "ix_tarea_materia" in indexes


# ---------------------------------------------------------------------------
# Grupo 3: ComentarioTarea model
# ---------------------------------------------------------------------------


class TestComentarioTareaModel:
    """Task 2.1: creación de ComentarioTarea."""

    @pytest.mark.asyncio
    async def test_crear_comentario(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED: crear ComentarioTarea → persiste con tarea_id y autor_id."""
        from app.models.tarea import Tarea, ComentarioTarea

        assignee = await _crear_usuario(db_session, default_tenant.id, "a1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "a2@test.com")
        autor = await _crear_usuario(db_session, default_tenant.id, "autor@test.com")

        tarea = Tarea(
            tenant_id=default_tenant.id,
            titulo="Tarea con comentario",
            asignado_a=assignee.id,
            asignado_por=assigner.id,
        )
        db_session.add(tarea)
        await db_session.commit()
        await db_session.refresh(tarea)

        comentario = ComentarioTarea(
            tenant_id=default_tenant.id,
            tarea_id=tarea.id,
            autor_id=autor.id,
            contenido="Este es un comentario",
        )
        db_session.add(comentario)
        await db_session.commit()
        await db_session.refresh(comentario)

        assert comentario.id is not None
        assert comentario.tarea_id == tarea.id
        assert comentario.autor_id == autor.id
        assert comentario.contenido == "Este es un comentario"
        assert comentario.deleted_at is None

    @pytest.mark.asyncio
    async def test_comentario_soft_delete(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN: soft delete de comentario setea deleted_at."""
        from app.models.tarea import Tarea, ComentarioTarea

        assignee = await _crear_usuario(db_session, default_tenant.id, "b1@test.com")
        assigner = await _crear_usuario(db_session, default_tenant.id, "b2@test.com")
        autor = await _crear_usuario(db_session, default_tenant.id, "b3@test.com")

        tarea = Tarea(
            tenant_id=default_tenant.id,
            titulo="Tarea",
            asignado_a=assignee.id,
            asignado_por=assigner.id,
        )
        db_session.add(tarea)
        await db_session.commit()
        await db_session.refresh(tarea)

        comentario = ComentarioTarea(
            tenant_id=default_tenant.id,
            tarea_id=tarea.id,
            autor_id=autor.id,
            contenido="Borrar",
        )
        db_session.add(comentario)
        await db_session.commit()
        await db_session.refresh(comentario)

        comentario.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(comentario)

        assert comentario.deleted_at is not None

    @pytest.mark.asyncio
    async def test_comentario_index_exists(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: índice de comentario existe."""
        result = await db_session.execute(
            text(
                """
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'comentario_tarea'
                AND schemaname = 'public'
                """
            )
        )
        indexes = {row[0] for row in result.all()}
        assert "ix_comentario_tarea_tarea" in indexes


# ---------------------------------------------------------------------------
# Grupo 4: Audit actions
# ---------------------------------------------------------------------------


class TestAuditActions:
    """Task 1.2: validación de nuevos audit actions."""

    def test_tarea_audit_actions_exist(self) -> None:
        """RED: AuditAction tiene los 9 TAREA_* entries."""
        from app.core.audit import AuditAction

        assert AuditAction.TAREA_CREAR == "TAREA_CREAR"
        assert AuditAction.TAREA_ACTUALIZAR == "TAREA_ACTUALIZAR"
        assert AuditAction.TAREA_ELIMINAR == "TAREA_ELIMINAR"
        assert AuditAction.TAREA_ESTADO_CAMBIAR == "TAREA_ESTADO_CAMBIAR"
        assert AuditAction.TAREA_APROBAR == "TAREA_APROBAR"
        assert AuditAction.TAREA_DEVOLVER == "TAREA_DEVOLVER"
        assert AuditAction.TAREA_DELEGAR == "TAREA_DELEGAR"
        assert AuditAction.TAREA_COMENTAR == "TAREA_COMENTAR"
        assert AuditAction.TAREA_COMENTARIO_ELIMINAR == "TAREA_COMENTARIO_ELIMINAR"
