"""Tests TDD para TareaService (C-16).

Strict TDD: RED → GREEN → TRIANGULATE.
Tests usan DB real (sin mocks — regla dura).
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
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


async def _crear_tarea_service(db_session, tenant_id, usuario_id, **kwargs):
    from app.services.tarea_service import TareaService
    svc = TareaService(db_session, tenant_id, usuario_id)
    data = {
        "titulo": kwargs.get("titulo", "Tarea"),
        "asignado_a": kwargs.get("asignado_a"),
        "asignado_por": kwargs.get("asignado_por", usuario_id),
    }
    if "descripcion" in kwargs:
        data["descripcion"] = kwargs["descripcion"]
    if "criterio_cierre" in kwargs:
        data["criterio_cierre"] = kwargs["criterio_cierre"]
    if "materia_id" in kwargs:
        data["materia_id"] = kwargs["materia_id"]
    return await svc.crear(data)


# ---------------------------------------------------------------------------
# Grupo 1: CRUD
# ---------------------------------------------------------------------------


class TestTareaServiceCRUD:
    """Task 5.2: CRUD operations."""

    @pytest.mark.asyncio
    async def test_crear_tarea(self, db_session: AsyncSession, default_tenant):
        """RED: crear tarea → persiste y audita."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea
        from app.models.audit_log import AuditLog

        assigner = await _crear_usuario(db_session, default_tenant.id, "creator@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "assignee@test.com")
        svc = TareaService(db_session, default_tenant.id, assigner.id)

        result = await svc.crear({
            "titulo": "Nueva tarea",
            "descripcion": "Desc",
            "asignado_a": assignee.id,
            "asignado_por": assigner.id,
        })

        assert result.titulo == "Nueva tarea"
        assert result.estado == EstadoTarea.PENDIENTE
        assert result.asignado_a == assignee.id

        # Audit
        audit = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "TAREA_CREAR")
        )
        assert audit.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_get_tarea(self, db_session: AsyncSession, default_tenant):
        """GREEN: get_tarea devuelve tarea."""
        from app.services.tarea_service import TareaService

        assigner = await _crear_usuario(db_session, default_tenant.id, "g1@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "g2@test.com")
        svc = TareaService(db_session, default_tenant.id, assigner.id)
        created = await svc.crear({"titulo": "Buscar", "asignado_a": assignee.id, "asignado_por": assigner.id})

        result = await svc.get_tarea(created.id)
        assert result.id == created.id

    @pytest.mark.asyncio
    async def test_get_tarea_not_found(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: get_tarea 404."""
        from app.services.tarea_service import TareaService

        svc = TareaService(db_session, default_tenant.id, uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await svc.get_tarea(uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_tarea(self, db_session: AsyncSession, default_tenant):
        """GREEN: update_tarea modifica y audita."""
        from app.services.tarea_service import TareaService
        from app.models.audit_log import AuditLog

        assigner = await _crear_usuario(db_session, default_tenant.id, "u1@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "u2@test.com")
        svc = TareaService(db_session, default_tenant.id, assigner.id)
        created = await svc.crear({"titulo": "Original", "asignado_a": assignee.id, "asignado_por": assigner.id})

        result = await svc.update_tarea(created.id, {"titulo": "Actualizado"})
        assert result.titulo == "Actualizado"

        audit = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "TAREA_ACTUALIZAR")
        )
        assert audit.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_delete_tarea(self, db_session: AsyncSession, default_tenant):
        """GREEN: delete_tarea soft delete y audita."""
        from app.services.tarea_service import TareaService
        from app.models.audit_log import AuditLog

        assigner = await _crear_usuario(db_session, default_tenant.id, "d1@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "d2@test.com")
        svc = TareaService(db_session, default_tenant.id, assigner.id)
        created = await svc.crear({"titulo": "Eliminar", "asignado_a": assignee.id, "asignado_por": assigner.id})

        result = await svc.delete_tarea(created.id)
        assert result.id == created.id

        audit = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "TAREA_ELIMINAR")
        )
        assert audit.scalar_one_or_none() is not None


# ---------------------------------------------------------------------------
# Grupo 2: State Machine
# ---------------------------------------------------------------------------


class TestTareaServiceStateMachine:
    """Task 5.1: validación de transiciones de estado."""

    @pytest.mark.asyncio
    async def test_pendiente_a_en_progreso(self, db_session: AsyncSession, default_tenant):
        """RED: Pendiente → En progreso (assignee)."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea

        assigner = await _crear_usuario(db_session, default_tenant.id, "s1@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "s2@test.com")
        svc = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})

        result = await svc.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, assignee.id)
        assert result.estado == EstadoTarea.EN_PROGRESO

    @pytest.mark.asyncio
    async def test_en_progreso_a_resuelta(self, db_session: AsyncSession, default_tenant):
        """GREEN: En progreso → Resuelta (assignee)."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea

        assigner = await _crear_usuario(db_session, default_tenant.id, "s3@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "s4@test.com")
        svc = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, assignee.id)

        result = await svc.cambiar_estado(created.id, EstadoTarea.RESUELTA, assignee.id)
        assert result.estado == EstadoTarea.RESUELTA

    @pytest.mark.asyncio
    async def test_en_progreso_a_cancelada(self, db_session: AsyncSession, default_tenant):
        """GREEN: En progreso → Cancelada (assignee o assigner)."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea

        assigner = await _crear_usuario(db_session, default_tenant.id, "s5@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "s6@test.com")
        svc = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, assignee.id)

        result = await svc.cambiar_estado(created.id, EstadoTarea.CANCELADA, assignee.id)
        assert result.estado == EstadoTarea.CANCELADA

    @pytest.mark.asyncio
    async def test_resuelta_a_en_progreso_por_devolver(self, db_session: AsyncSession, default_tenant):
        """GREEN: Resuelta → En progreso vía devolver (assigner)."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea

        assigner = await _crear_usuario(db_session, default_tenant.id, "s7@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "s8@test.com")
        svc_assignee = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc_assignee.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc_assignee.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, assignee.id)
        await svc_assignee.cambiar_estado(created.id, EstadoTarea.RESUELTA, assignee.id)

        svc_assigner = TareaService(db_session, default_tenant.id, assigner.id)
        result = await svc_assigner.devolver(created.id, "Necesita rework")
        assert result.estado == EstadoTarea.EN_PROGRESO
        assert result.devuelta is True

    @pytest.mark.asyncio
    async def test_aprobar_tarea(self, db_session: AsyncSession, default_tenant):
        """GREEN: aprobar Resuelta → aprobada=True."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea

        assigner = await _crear_usuario(db_session, default_tenant.id, "s9@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "s10@test.com")
        svc_assignee = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc_assignee.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc_assignee.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, assignee.id)
        await svc_assignee.cambiar_estado(created.id, EstadoTarea.RESUELTA, assignee.id)

        svc_assigner = TareaService(db_session, default_tenant.id, assigner.id)
        result = await svc_assigner.aprobar(created.id)
        assert result.aprobada is True
        assert result.revisada_por == assigner.id
        assert result.revisada_at is not None

    @pytest.mark.asyncio
    async def test_invalid_transition_resuelta_a_en_progreso_directo(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: Resuelta → En progreso directo sin devolver = 422."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea

        assigner = await _crear_usuario(db_session, default_tenant.id, "s11@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "s12@test.com")
        svc = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, assignee.id)
        await svc.cambiar_estado(created.id, EstadoTarea.RESUELTA, assignee.id)

        with pytest.raises(HTTPException) as exc_info:
            await svc.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, assignee.id)
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_transition_pendiente_a_resuelta(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: Pendiente → Resuelta = 422."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea

        assigner = await _crear_usuario(db_session, default_tenant.id, "s13@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "s14@test.com")
        svc = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})

        with pytest.raises(HTTPException) as exc_info:
            await svc.cambiar_estado(created.id, EstadoTarea.RESUELTA, assignee.id)
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthorized_state_change(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: usuario no asignado ni asignador = 403."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea

        assigner = await _crear_usuario(db_session, default_tenant.id, "s15@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "s16@test.com")
        intruso = await _crear_usuario(db_session, default_tenant.id, "s17@test.com")
        svc = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})

        svc_intruso = TareaService(db_session, default_tenant.id, intruso.id)
        with pytest.raises(HTTPException) as exc_info:
            await svc_intruso.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, intruso.id)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_aprobar_non_resuelta_422(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: aprobar non-Resuelta = 422."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea

        assigner = await _crear_usuario(db_session, default_tenant.id, "s18@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "s19@test.com")
        svc = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, assignee.id)

        svc_assigner = TareaService(db_session, default_tenant.id, assigner.id)
        with pytest.raises(HTTPException) as exc_info:
            await svc_assigner.aprobar(created.id)
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_devolver_non_resuelta_422(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: devolver non-Resuelta = 422."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea

        assigner = await _crear_usuario(db_session, default_tenant.id, "s20@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "s21@test.com")
        svc = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})

        svc_assigner = TareaService(db_session, default_tenant.id, assigner.id)
        with pytest.raises(HTTPException) as exc_info:
            await svc_assigner.devolver(created.id, "Obs")
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# Grupo 3: Delegación
# ---------------------------------------------------------------------------


class TestTareaServiceDelegacion:
    """Task 5.2: delegación."""

    @pytest.mark.asyncio
    async def test_delegar_tarea(self, db_session: AsyncSession, default_tenant):
        """RED: delegar reasigna asignado_a."""
        from app.services.tarea_service import TareaService

        assigner = await _crear_usuario(db_session, default_tenant.id, "del1@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "del2@test.com")
        nuevo = await _crear_usuario(db_session, default_tenant.id, "del3@test.com")
        svc = TareaService(db_session, default_tenant.id, assigner.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})

        result = await svc.delegar(created.id, nuevo.id)
        assert result.asignado_a == nuevo.id


# ---------------------------------------------------------------------------
# Grupo 4: Comentarios
# ---------------------------------------------------------------------------


class TestTareaServiceComentarios:
    """Task 5.2: comentarios."""

    @pytest.mark.asyncio
    async def test_crear_comentario(self, db_session: AsyncSession, default_tenant):
        """RED: crear comentario → persiste y audita."""
        from app.services.tarea_service import TareaService
        from app.models.audit_log import AuditLog

        assigner = await _crear_usuario(db_session, default_tenant.id, "c1@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "c2@test.com")
        autor = await _crear_usuario(db_session, default_tenant.id, "c3@test.com")
        svc = TareaService(db_session, default_tenant.id, assigner.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})

        result = await svc.crear_comentario(created.id, {"contenido": "Comentario"})
        assert result.contenido == "Comentario"
        assert result.tarea_id == created.id

        audit = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "TAREA_COMENTAR")
        )
        assert audit.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_list_comentarios(self, db_session: AsyncSession, default_tenant):
        """GREEN: listar comentarios paginados."""
        from app.services.tarea_service import TareaService

        assigner = await _crear_usuario(db_session, default_tenant.id, "c4@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "c5@test.com")
        svc = TareaService(db_session, default_tenant.id, assigner.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc.crear_comentario(created.id, {"contenido": "C1"})
        await svc.crear_comentario(created.id, {"contenido": "C2"})

        result = await svc.list_comentarios(created.id, page=1, page_size=10)
        assert result.total == 2
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_delete_comentario(self, db_session: AsyncSession, default_tenant):
        """GREEN: delete_comentario soft delete y audita."""
        from app.services.tarea_service import TareaService
        from app.models.audit_log import AuditLog

        assigner = await _crear_usuario(db_session, default_tenant.id, "c6@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "c7@test.com")
        svc = TareaService(db_session, default_tenant.id, assigner.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        comentario = await svc.crear_comentario(created.id, {"contenido": "Borrar"})

        result = await svc.delete_comentario(comentario.id)
        assert result.id == comentario.id

        audit = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "TAREA_COMENTARIO_ELIMINAR")
        )
        assert audit.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_delete_comentario_no_autor_403(self, db_session: AsyncSession, default_tenant):
        """RED: non-author deleting comment must get 403."""
        from app.services.tarea_service import TareaService

        assigner = await _crear_usuario(db_session, default_tenant.id, "c8@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "c9@test.com")
        other = await _crear_usuario(db_session, default_tenant.id, "c10@test.com")
        svc_assigner = TareaService(db_session, default_tenant.id, assigner.id)
        created = await svc_assigner.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        comentario = await svc_assigner.crear_comentario(created.id, {"contenido": "Borrar"})

        svc_other = TareaService(db_session, default_tenant.id, other.id)
        with pytest.raises(HTTPException) as exc:
            await svc_other.delete_comentario(comentario.id)
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Grupo 5: Listados
# ---------------------------------------------------------------------------


class TestTareaServiceListados:
    """Task 5.2: listados."""

    @pytest.mark.asyncio
    async def test_list_admin(self, db_session: AsyncSession, default_tenant):
        """RED: list_admin devuelve tareas del tenant."""
        from app.services.tarea_service import TareaService

        assigner = await _crear_usuario(db_session, default_tenant.id, "l1@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "l2@test.com")
        svc = TareaService(db_session, default_tenant.id, assigner.id)
        await svc.crear({"titulo": "T1", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc.crear({"titulo": "T2", "asignado_a": assignee.id, "asignado_por": assigner.id})

        result = await svc.list_admin({}, page=1, page_size=10)
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_list_mis_tareas(self, db_session: AsyncSession, default_tenant):
        """GREEN: list_mis_tareas filtra por asignado_a."""
        from app.services.tarea_service import TareaService

        assigner = await _crear_usuario(db_session, default_tenant.id, "m1@test.com")
        a1 = await _crear_usuario(db_session, default_tenant.id, "m2@test.com")
        a2 = await _crear_usuario(db_session, default_tenant.id, "m3@test.com")
        svc = TareaService(db_session, default_tenant.id, assigner.id)
        await svc.crear({"titulo": "T1", "asignado_a": a1.id, "asignado_por": assigner.id})
        await svc.crear({"titulo": "T2", "asignado_a": a2.id, "asignado_por": assigner.id})

        svc_a1 = TareaService(db_session, default_tenant.id, a1.id)
        result = await svc_a1.list_mis_tareas(page=1, page_size=10)
        assert result.total == 1
        assert result.items[0].titulo == "T1"

    @pytest.mark.asyncio
    async def test_list_mis_tareas_filter_estado(self, db_session: AsyncSession, default_tenant):
        """TRIANGULATE: list_mis_tareas con filtro estado."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea

        assigner = await _crear_usuario(db_session, default_tenant.id, "n1@test.com")
        a1 = await _crear_usuario(db_session, default_tenant.id, "n2@test.com")
        svc = TareaService(db_session, default_tenant.id, a1.id)
        t1 = await svc.crear({"titulo": "T1", "asignado_a": a1.id, "asignado_por": assigner.id})
        # estado default = Pendiente

        result = await svc.list_mis_tareas(page=1, page_size=10, estado=EstadoTarea.PENDIENTE)
        assert result.total == 1

        result2 = await svc.list_mis_tareas(page=1, page_size=10, estado=EstadoTarea.EN_PROGRESO)
        assert result2.total == 0


# ---------------------------------------------------------------------------
# Grupo 6: Audit
# ---------------------------------------------------------------------------


class TestTareaServiceAudit:
    """Task 5.2: verificación de audit entries."""

    @pytest.mark.asyncio
    async def test_audit_estado_cambiar(self, db_session: AsyncSession, default_tenant):
        """RED: cambiar estado genera audit TAREA_ESTADO_CAMBIAR."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea
        from app.models.audit_log import AuditLog

        assigner = await _crear_usuario(db_session, default_tenant.id, "a1@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "a2@test.com")
        svc = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, assignee.id)

        audit = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "TAREA_ESTADO_CAMBIAR")
        )
        assert audit.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_audit_delegar(self, db_session: AsyncSession, default_tenant):
        """GREEN: delegar genera audit TAREA_DELEGAR."""
        from app.services.tarea_service import TareaService
        from app.models.audit_log import AuditLog

        assigner = await _crear_usuario(db_session, default_tenant.id, "a3@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "a4@test.com")
        nuevo = await _crear_usuario(db_session, default_tenant.id, "a5@test.com")
        svc = TareaService(db_session, default_tenant.id, assigner.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc.delegar(created.id, nuevo.id)

        audit = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "TAREA_DELEGAR")
        )
        assert audit.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_audit_aprobar(self, db_session: AsyncSession, default_tenant):
        """GREEN: aprobar genera audit TAREA_APROBAR."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea
        from app.models.audit_log import AuditLog

        assigner = await _crear_usuario(db_session, default_tenant.id, "a6@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "a7@test.com")
        svc = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, assignee.id)
        await svc.cambiar_estado(created.id, EstadoTarea.RESUELTA, assignee.id)

        svc_assigner = TareaService(db_session, default_tenant.id, assigner.id)
        await svc_assigner.aprobar(created.id)

        audit = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "TAREA_APROBAR")
        )
        assert audit.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_audit_devolver(self, db_session: AsyncSession, default_tenant):
        """GREEN: devolver genera audit TAREA_DEVOLVER."""
        from app.services.tarea_service import TareaService
        from app.models.tarea import EstadoTarea
        from app.models.audit_log import AuditLog

        assigner = await _crear_usuario(db_session, default_tenant.id, "a8@test.com")
        assignee = await _crear_usuario(db_session, default_tenant.id, "a9@test.com")
        svc = TareaService(db_session, default_tenant.id, assignee.id)
        created = await svc.crear({"titulo": "Tarea", "asignado_a": assignee.id, "asignado_por": assigner.id})
        await svc.cambiar_estado(created.id, EstadoTarea.EN_PROGRESO, assignee.id)
        await svc.cambiar_estado(created.id, EstadoTarea.RESUELTA, assignee.id)

        svc_assigner = TareaService(db_session, default_tenant.id, assigner.id)
        await svc_assigner.devolver(created.id, "Obs")

        audit = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "TAREA_DEVOLVER")
        )
        assert audit.scalar_one_or_none() is not None
