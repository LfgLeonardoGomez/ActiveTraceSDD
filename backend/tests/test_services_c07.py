"""Tests TDD para servicios C-07: UsuarioService y AsignacionService.

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Tests usan DB real (sin mocks — regla dura).
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4, UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================
# GRUPO 7: UsuarioService
# ============================================================


class TestUsuarioServiceUnicidadEmail:
    """Task 7.1 RED → GREEN → TRIANGULATE: unicidad email en service."""

    @pytest.mark.asyncio
    async def test_usuario_service_crear_unicidad_email_mismo_tenant(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 7.1: crear dos usuarios con mismo email en mismo tenant → 409."""
        from app.services.usuarios import UsuarioService

        service = UsuarioService(db_session, default_tenant.id)
        await service.crear_usuario(
            nombre="Primero",
            apellidos="Test",
            email="duplicado.svc@test.com",
            estado="Activo",
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.crear_usuario(
                nombre="Segundo",
                apellidos="Test",
                email="duplicado.svc@test.com",
                estado="Activo",
            )
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_usuario_service_crear_unicidad_email_tenant_diferente_ok(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 7.1: mismo email en tenant distinto → OK."""
        from app.models.tenant import Tenant
        from app.services.usuarios import UsuarioService

        import uuid as _uuid
        tenant_b = Tenant(nombre="Tenant B Svc", slug=f"tenant-b-svc-c07-{_uuid.uuid4().hex[:8]}", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        svc_a = UsuarioService(db_session, default_tenant.id)
        await svc_a.crear_usuario(
            nombre="Alice",
            apellidos="Svc",
            email="shared.svc@test.com",
            estado="Activo",
        )

        svc_b = UsuarioService(db_session, tenant_b.id)
        u_b = await svc_b.crear_usuario(
            nombre="Bob",
            apellidos="Svc",
            email="shared.svc@test.com",
            estado="Activo",
        )
        assert u_b is not None
        assert u_b.email == "shared.svc@test.com"

    @pytest.mark.asyncio
    async def test_usuario_service_crear_exitoso(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 7.2: crear usuario sin conflicto."""
        from app.services.usuarios import UsuarioService

        service = UsuarioService(db_session, default_tenant.id)
        usuario = await service.crear_usuario(
            nombre="Nuevo",
            apellidos="Usuario",
            email="nuevo@test.com",
            estado="Activo",
        )
        assert usuario.nombre == "Nuevo"
        assert usuario.email == "nuevo@test.com"

    @pytest.mark.asyncio
    async def test_usuario_service_listar_usuarios(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 7.2: listar_usuarios retorna paginado."""
        from app.services.usuarios import UsuarioService

        service = UsuarioService(db_session, default_tenant.id)
        await service.crear_usuario(nombre="L1", apellidos="T", email="l1list@test.com", estado="Activo")
        await service.crear_usuario(nombre="L2", apellidos="T", email="l2list@test.com", estado="Activo")

        items, total = await service.listar_usuarios(limit=10, offset=0)
        assert total >= 2

    @pytest.mark.asyncio
    async def test_usuario_service_obtener_usuario_ok(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 7.2: obtener_usuario retorna el usuario."""
        from app.services.usuarios import UsuarioService

        service = UsuarioService(db_session, default_tenant.id)
        creado = await service.crear_usuario(
            nombre="GetMe", apellidos="T", email="getme@test.com", estado="Activo"
        )
        encontrado = await service.obtener_usuario(creado.id)
        assert encontrado.id == creado.id

    @pytest.mark.asyncio
    async def test_usuario_service_obtener_usuario_404(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 7.2: obtener_usuario con ID inexistente → 404."""
        from app.services.usuarios import UsuarioService

        service = UsuarioService(db_session, default_tenant.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.obtener_usuario(uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_usuario_service_actualizar_email_unicidad(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 7.3: actualizar email a uno ya existente → 409."""
        from app.services.usuarios import UsuarioService

        service = UsuarioService(db_session, default_tenant.id)
        await service.crear_usuario(
            nombre="ExistingEmail", apellidos="T", email="existing@test.com", estado="Activo"
        )
        u2 = await service.crear_usuario(
            nombre="ToUpdate", apellidos="T", email="toupdate@test.com", estado="Activo"
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.actualizar_usuario(u2.id, {"email": "existing@test.com"})
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_usuario_service_eliminar_usuario(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 7.2: eliminar_usuario realiza soft delete."""
        from app.services.usuarios import UsuarioService

        service = UsuarioService(db_session, default_tenant.id)
        usuario = await service.crear_usuario(
            nombre="ToDelete", apellidos="T", email="todelete@test.com", estado="Activo"
        )
        result = await service.eliminar_usuario(usuario.id)
        assert result is True


class TestUsuarioServicePiiNoExpuesta:
    """Task 7.4 RED → GREEN: PII no expuesta en mensajes de error."""

    @pytest.mark.asyncio
    async def test_usuario_service_pii_no_expuesta_en_error_409(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 7.4: el 409 por email duplicado NO contiene el email en texto plano."""
        from app.services.usuarios import UsuarioService

        service = UsuarioService(db_session, default_tenant.id)
        email = "pii.noexpuesta@test.com"
        await service.crear_usuario(
            nombre="Primero", apellidos="T", email=email, estado="Activo"
        )

        try:
            await service.crear_usuario(
                nombre="Segundo", apellidos="T", email=email, estado="Activo"
            )
            pytest.fail("Debería haber lanzado HTTPException")
        except HTTPException as exc:
            # El mensaje de error NO debe contener el email en texto plano
            error_detail = str(exc.detail)
            assert email not in error_detail, (
                f"PII expuesta en error: '{email}' found in '{error_detail}'"
            )
            assert exc.status_code == 409


# ============================================================
# GRUPO 8: AsignacionService
# ============================================================


class TestAsignacionServiceVigencia:
    """Task 8.1 RED → GREEN → TRIANGULATE: vigencia en asignaciones."""

    @pytest.mark.asyncio
    async def test_asignacion_service_vigencia_vigente(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 8.1: asignación dentro del rango de fechas → Vigente."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        usuario = await usuario_svc.crear_usuario(
            nombre="ProfesorV", apellidos="Test", email="profesor.v@test.com", estado="Activo"
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
    async def test_asignacion_service_vigencia_vencida(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 8.2: asignación con hasta en el pasado → Vencida."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        usuario = await usuario_svc.crear_usuario(
            nombre="ProfesorVenc", apellidos="Test", email="profesor.venc@test.com", estado="Activo"
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
    async def test_asignacion_service_vigencia_sin_hasta(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 8.1: sin hasta → Vigente."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        usuario = await usuario_svc.crear_usuario(
            nombre="ProfesorSH", apellidos="Test", email="profesor.sh@test.com", estado="Activo"
        )

        asig_svc = AsignacionService(db_session, default_tenant.id)
        asig = await asig_svc.crear_asignacion(
            usuario_id=usuario.id,
            rol="ADMIN",
            desde=date.today() - timedelta(days=1),
            hasta=None,
        )
        assert asig.estado_vigencia == "Vigente"

    @pytest.mark.asyncio
    async def test_asignacion_service_vigencia_futura(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 8.1: desde en el futuro → Vencida."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        usuario = await usuario_svc.crear_usuario(
            nombre="ProfesorFut", apellidos="Test", email="profesor.fut@test.com", estado="Activo"
        )

        asig_svc = AsignacionService(db_session, default_tenant.id)
        asig = await asig_svc.crear_asignacion(
            usuario_id=usuario.id,
            rol="NEXO",
            desde=date.today() + timedelta(days=5),
            hasta=date.today() + timedelta(days=30),
        )
        assert asig.estado_vigencia == "Vencida"


class TestAsignacionServiceMultiRol:
    """Task 8.4 RED → GREEN: múltiples asignaciones simultáneas para un usuario."""

    @pytest.mark.asyncio
    async def test_asignacion_multi_rol_usuario(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 8.4: usuario con múltiples asignaciones simultáneas → OK."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        usuario = await usuario_svc.crear_usuario(
            nombre="MultiRol", apellidos="Test", email="multirrol@test.com", estado="Activo"
        )

        asig_svc = AsignacionService(db_session, default_tenant.id)
        a1 = await asig_svc.crear_asignacion(
            usuario_id=usuario.id,
            rol="PROFESOR",
            desde=date.today(),
        )
        a2 = await asig_svc.crear_asignacion(
            usuario_id=usuario.id,
            rol="TUTOR",
            desde=date.today(),
        )

        assert a1.id != a2.id
        assert a1.rol == "PROFESOR"
        assert a2.rol == "TUTOR"

    @pytest.mark.asyncio
    async def test_asignacion_service_listar_por_usuario(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 8.2: listar asignaciones de un usuario específico."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        u1 = await usuario_svc.crear_usuario(
            nombre="ListU1", apellidos="T", email="listu1@test.com", estado="Activo"
        )
        u2 = await usuario_svc.crear_usuario(
            nombre="ListU2", apellidos="T", email="listu2@test.com", estado="Activo"
        )

        asig_svc = AsignacionService(db_session, default_tenant.id)
        a1 = await asig_svc.crear_asignacion(usuario_id=u1.id, rol="PROFESOR", desde=date.today())
        a2 = await asig_svc.crear_asignacion(usuario_id=u2.id, rol="TUTOR", desde=date.today())

        items, total = await asig_svc.listar_asignaciones(usuario_id=u1.id)
        ids = {a.id for a in items}
        assert a1.id in ids
        assert a2.id not in ids

    @pytest.mark.asyncio
    async def test_asignacion_service_obtener_404(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 8.2: obtener_asignacion con ID inexistente → 404."""
        from app.services.asignaciones import AsignacionService

        svc = AsignacionService(db_session, default_tenant.id)
        with pytest.raises(HTTPException) as exc_info:
            await svc.obtener_asignacion(uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_asignacion_service_eliminar(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 8.2: eliminar_asignacion soft delete."""
        from app.services.usuarios import UsuarioService
        from app.services.asignaciones import AsignacionService

        usuario_svc = UsuarioService(db_session, default_tenant.id)
        usuario = await usuario_svc.crear_usuario(
            nombre="ElimAsig", apellidos="T", email="elimasig@test.com", estado="Activo"
        )

        asig_svc = AsignacionService(db_session, default_tenant.id)
        asig = await asig_svc.crear_asignacion(usuario_id=usuario.id, rol="NEXO", desde=date.today())
        result = await asig_svc.eliminar_asignacion(asig.id)
        assert result is True
