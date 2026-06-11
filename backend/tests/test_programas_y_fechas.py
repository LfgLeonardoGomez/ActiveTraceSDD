"""Tests para programas y fechas académicas (C-17).

Strict TDD: RED → GREEN → TRIANGULATE.
Tests usan DB real (sin mocks — regla dura).
"""

import pytest
from datetime import date, datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _crear_tenant_y_materia(db_session: AsyncSession):
    """Crea tenant, carrera, cohorte y materia para tests."""
    from app.models.tenant import Tenant
    from app.models.estructura import Carrera, Cohorte, Materia

    tenant = Tenant(nombre="Test Tenant", slug="test", activo=True)
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)

    carrera = Carrera(
        tenant_id=tenant.id,
        codigo="TUPAD",
        nombre="Tecnicatura Universitaria en Programación",
        estado="Activa",
    )
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    cohorte = Cohorte(
        tenant_id=tenant.id,
        carrera_id=carrera.id,
        nombre="AGO-2025",
        anio=2025,
        vig_desde=date(2025, 8, 1),
        estado="Activa",
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)

    materia = Materia(
        tenant_id=tenant.id,
        codigo="PROG_I",
        nombre="Programación I",
        estado="Activa",
    )
    db_session.add(materia)
    await db_session.commit()
    await db_session.refresh(materia)

    return tenant, carrera, cohorte, materia


async def _crear_usuario(db_session: AsyncSession, tenant_id, email: str = "admin@test.com"):
    from app.models.user import Usuario
    from app.core import security
    u = Usuario(
        tenant_id=tenant_id,
        nombre="Admin",
        apellidos="Test",
        email=email,
        estado="activo",
        password_hash=security.hash_password("Pass1234"),
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _crear_programa_service(db_session, tenant_id, usuario_id, materia_id, carrera_id, cohorte_id, **kwargs):
    from app.services.programa_materia_service import ProgramaMateriaService
    svc = ProgramaMateriaService(db_session, tenant_id, usuario_id)
    data = {
        "materia_id": materia_id,
        "carrera_id": carrera_id,
        "cohorte_id": cohorte_id,
        "titulo": kwargs.get("titulo", "Programa de prueba"),
        "referencia_archivo": kwargs.get("referencia_archivo", "s3://bucket/programa.pdf"),
    }
    return await svc.crear_programa(data)


async def _crear_fecha_service(db_session, tenant_id, usuario_id, materia_id, cohorte_id, **kwargs):
    from app.services.programa_materia_service import FechaAcademicaService
    svc = FechaAcademicaService(db_session, tenant_id, usuario_id)
    data = {
        "materia_id": materia_id,
        "cohorte_id": cohorte_id,
        "tipo": kwargs.get("tipo", "Parcial"),
        "numero": kwargs.get("numero", 1),
        "periodo": kwargs.get("periodo", "2025-2"),
        "fecha": kwargs.get("fecha", date(2025, 10, 15)),
        "titulo": kwargs.get("titulo", "1er Parcial"),
    }
    return await svc.crear_fecha(data)


# ---------------------------------------------------------------------------
# Grupo 1: Schemas
# ---------------------------------------------------------------------------


class TestProgramaMateriaSchemas:
    """Task 3.1: validación de schemas ProgramaMateria."""

    def test_programa_create_requiere_campos_obligatorios(self) -> None:
        """RED: ProgramaMateriaCreate requiere campos obligatorios."""
        from pydantic import ValidationError
        from app.schemas.programa_materia import ProgramaMateriaCreateSchema

        with pytest.raises(ValidationError):
            ProgramaMateriaCreateSchema(titulo="Solo título")

    def test_programa_create_valido(self) -> None:
        """GREEN: ProgramaMateriaCreate acepta campos correctos."""
        from app.schemas.programa_materia import ProgramaMateriaCreateSchema

        materia_id = uuid4()
        carrera_id = uuid4()
        cohorte_id = uuid4()
        obj = ProgramaMateriaCreateSchema(
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            titulo="Programa de Programación I",
            referencia_archivo="s3://bucket/programa.pdf",
        )
        assert obj.titulo == "Programa de Programación I"
        assert obj.referencia_archivo == "s3://bucket/programa.pdf"

    def test_programa_create_rechaza_campos_extra(self) -> None:
        """GREEN: ProgramaMateriaCreate rechaza campos extra (extra='forbid')."""
        from pydantic import ValidationError
        from app.schemas.programa_materia import ProgramaMateriaCreateSchema

        with pytest.raises(ValidationError):
            ProgramaMateriaCreateSchema(
                materia_id=uuid4(),
                carrera_id=uuid4(),
                cohorte_id=uuid4(),
                titulo="Programa",
                referencia_archivo="s3://bucket/programa.pdf",
                campo_extra="x",
            )

    def test_programa_response_schema(self) -> None:
        """GREEN: ProgramaMateriaResponseSchema incluye todos los campos."""
        from app.schemas.programa_materia import ProgramaMateriaResponseSchema

        now = datetime.now(timezone.utc)
        obj = ProgramaMateriaResponseSchema(
            id=uuid4(),
            tenant_id=uuid4(),
            materia_id=uuid4(),
            carrera_id=uuid4(),
            cohorte_id=uuid4(),
            titulo="Programa",
            referencia_archivo="s3://bucket/programa.pdf",
            cargado_at=now,
            created_at=now,
            updated_at=now,
        )
        assert obj.titulo == "Programa"
        assert obj.cargado_at is not None


class TestFechaAcademicaSchemas:
    """Task 3.2: validación de schemas FechaAcademica."""

    def test_fecha_create_requiere_campos_obligatorios(self) -> None:
        """RED: FechaAcademicaCreate requiere campos obligatorios."""
        from pydantic import ValidationError
        from app.schemas.programa_materia import FechaAcademicaCreateSchema

        with pytest.raises(ValidationError):
            FechaAcademicaCreateSchema(titulo="Solo título")

    def test_fecha_create_valido(self) -> None:
        """GREEN: FechaAcademicaCreate acepta campos correctos."""
        from app.schemas.programa_materia import FechaAcademicaCreateSchema

        obj = FechaAcademicaCreateSchema(
            materia_id=uuid4(),
            cohorte_id=uuid4(),
            tipo="Parcial",
            numero=1,
            periodo="2025-2",
            fecha=date(2025, 10, 15),
            titulo="1er Parcial",
        )
        assert obj.tipo == "Parcial"
        assert obj.numero == 1

    def test_fecha_create_rechaza_campos_extra(self) -> None:
        """GREEN: FechaAcademicaCreate rechaza campos extra (extra='forbid')."""
        from pydantic import ValidationError
        from app.schemas.programa_materia import FechaAcademicaCreateSchema

        with pytest.raises(ValidationError):
            FechaAcademicaCreateSchema(
                materia_id=uuid4(),
                cohorte_id=uuid4(),
                tipo="Parcial",
                numero=1,
                periodo="2025-2",
                fecha=date(2025, 10, 15),
                titulo="1er Parcial",
                campo_extra="x",
            )


class TestLMSContentSchema:
    """Task 3.3: validación de schema LMSContent."""

    def test_lms_content_schema(self) -> None:
        """GREEN: LMSContentResponseSchema estructura correcta."""
        from app.schemas.programa_materia import LMSContentResponseSchema

        obj = LMSContentResponseSchema(
            materia_id=uuid4(),
            cohorte_id=uuid4(),
            html="<table></table>",
            cantidad_fechas=2,
        )
        assert obj.cantidad_fechas == 2
        assert "<table>" in obj.html


# ---------------------------------------------------------------------------
# Grupo 2: Service — ProgramaMateria CRUD
# ---------------------------------------------------------------------------


class TestProgramaMateriaServiceCRUD:
    """Task 4.1: CRUD de programas."""

    @pytest.mark.asyncio
    async def test_crear_programa(self, db_session: AsyncSession):
        """RED: crear programa → persiste y audita."""
        from app.services.programa_materia_service import ProgramaMateriaService
        from app.models.audit_log import AuditLog

        tenant, carrera, cohorte, materia = await _crear_tenant_y_materia(db_session)
        usuario = await _crear_usuario(db_session, tenant.id)
        svc = ProgramaMateriaService(db_session, tenant.id, usuario.id)

        result = await svc.crear_programa({
            "materia_id": materia.id,
            "carrera_id": carrera.id,
            "cohorte_id": cohorte.id,
            "titulo": "Programa de Programación I",
            "referencia_archivo": "s3://bucket/programa.pdf",
        })

        assert result.titulo == "Programa de Programación I"
        assert result.materia_id == materia.id

        # Audit
        audit = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "PROGRAMA_CREAR")
        )
        assert audit.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_crear_programa_conflicto_unicidad(self, db_session: AsyncSession):
        """RED: crear programa duplicado → 409."""
        from app.services.programa_materia_service import ProgramaMateriaService

        tenant, carrera, cohorte, materia = await _crear_tenant_y_materia(db_session)
        usuario = await _crear_usuario(db_session, tenant.id)
        svc = ProgramaMateriaService(db_session, tenant.id, usuario.id)

        await svc.crear_programa({
            "materia_id": materia.id,
            "carrera_id": carrera.id,
            "cohorte_id": cohorte.id,
            "titulo": "Programa 1",
            "referencia_archivo": "s3://bucket/programa1.pdf",
        })

        with pytest.raises(HTTPException) as exc_info:
            await svc.crear_programa({
                "materia_id": materia.id,
                "carrera_id": carrera.id,
                "cohorte_id": cohorte.id,
                "titulo": "Programa 2",
                "referencia_archivo": "s3://bucket/programa2.pdf",
            })
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_get_programa(self, db_session: AsyncSession):
        """GREEN: get_programa devuelve programa."""
        from app.services.programa_materia_service import ProgramaMateriaService

        tenant, carrera, cohorte, materia = await _crear_tenant_y_materia(db_session)
        usuario = await _crear_usuario(db_session, tenant.id)
        svc = ProgramaMateriaService(db_session, tenant.id, usuario.id)

        created = await _crear_programa_service(
            db_session, tenant.id, usuario.id, materia.id, carrera.id, cohorte.id
        )
        result = await svc.get_programa(created.id)
        assert result.id == created.id

    @pytest.mark.asyncio
    async def test_update_programa(self, db_session: AsyncSession):
        """GREEN: update_programa actualiza campos."""
        from app.services.programa_materia_service import ProgramaMateriaService

        tenant, carrera, cohorte, materia = await _crear_tenant_y_materia(db_session)
        usuario = await _crear_usuario(db_session, tenant.id)
        svc = ProgramaMateriaService(db_session, tenant.id, usuario.id)

        created = await _crear_programa_service(
            db_session, tenant.id, usuario.id, materia.id, carrera.id, cohorte.id
        )
        result = await svc.update_programa(created.id, {"titulo": "Programa actualizado"})
        assert result.titulo == "Programa actualizado"

    @pytest.mark.asyncio
    async def test_delete_programa(self, db_session: AsyncSession):
        """GREEN: delete_programa aplica soft delete."""
        from app.services.programa_materia_service import ProgramaMateriaService
        from app.models.programa_materia import ProgramaMateria

        tenant, carrera, cohorte, materia = await _crear_tenant_y_materia(db_session)
        usuario = await _crear_usuario(db_session, tenant.id)
        svc = ProgramaMateriaService(db_session, tenant.id, usuario.id)

        created = await _crear_programa_service(
            db_session, tenant.id, usuario.id, materia.id, carrera.id, cohorte.id
        )
        result = await svc.delete_programa(created.id)
        assert result.id == created.id

        # Verificar soft delete
        programa = await db_session.get(ProgramaMateria, created.id)
        assert programa.deleted_at is not None


# ---------------------------------------------------------------------------
# Grupo 3: Service — FechaAcademica CRUD
# ---------------------------------------------------------------------------


class TestFechaAcademicaServiceCRUD:
    """Task 4.2: CRUD de fechas académicas."""

    @pytest.mark.asyncio
    async def test_crear_fecha(self, db_session: AsyncSession):
        """RED: crear fecha → persiste y audita."""
        from app.services.programa_materia_service import FechaAcademicaService
        from app.models.audit_log import AuditLog

        tenant, carrera, cohorte, materia = await _crear_tenant_y_materia(db_session)
        usuario = await _crear_usuario(db_session, tenant.id)
        svc = FechaAcademicaService(db_session, tenant.id, usuario.id)

        result = await svc.crear_fecha({
            "materia_id": materia.id,
            "cohorte_id": cohorte.id,
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2025-2",
            "fecha": date(2025, 10, 15),
            "titulo": "1er Parcial",
        })

        assert result.tipo == "Parcial"
        assert result.numero == 1

        # Audit
        audit = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "FECHA_CREAR")
        )
        assert audit.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_list_fechas_por_cohorte(self, db_session: AsyncSession):
        """GREEN: list_fechas_por_cohorte ordena por tipo, numero, fecha."""
        from app.services.programa_materia_service import FechaAcademicaService

        tenant, carrera, cohorte, materia = await _crear_tenant_y_materia(db_session)
        usuario = await _crear_usuario(db_session, tenant.id)

        await _crear_fecha_service(db_session, tenant.id, usuario.id, materia.id, cohorte.id, tipo="TP", numero=1, fecha=date(2025, 9, 1))
        await _crear_fecha_service(db_session, tenant.id, usuario.id, materia.id, cohorte.id, tipo="Parcial", numero=1, fecha=date(2025, 10, 15))

        svc = FechaAcademicaService(db_session, tenant.id, usuario.id)
        result = await svc.list_fechas_por_cohorte(materia.id, cohorte.id, page=1, page_size=10)
        assert result.total == 2
        assert result.items[0].tipo == "Parcial"  # Orden alfabético

    @pytest.mark.asyncio
    async def test_delete_fecha(self, db_session: AsyncSession):
        """GREEN: delete_fecha aplica soft delete."""
        from app.services.programa_materia_service import FechaAcademicaService
        from app.models.programa_materia import FechaAcademica

        tenant, carrera, cohorte, materia = await _crear_tenant_y_materia(db_session)
        usuario = await _crear_usuario(db_session, tenant.id)
        svc = FechaAcademicaService(db_session, tenant.id, usuario.id)

        created = await _crear_fecha_service(db_session, tenant.id, usuario.id, materia.id, cohorte.id)
        result = await svc.delete_fecha(created.id)
        assert result.id == created.id

        # Verificar soft delete
        fecha = await db_session.get(FechaAcademica, created.id)
        assert fecha.deleted_at is not None


# ---------------------------------------------------------------------------
# Grupo 4: Service — Generación LMS
# ---------------------------------------------------------------------------


class TestGeneracionLMSService:
    """Task 4.3: generación de contenido LMS."""

    @pytest.mark.asyncio
    async def test_generar_lms_con_fechas(self, db_session: AsyncSession):
        """GREEN: generar_contenido_lms con fechas → tabla HTML."""
        from app.services.programa_materia_service import GeneracionLMSService

        tenant, carrera, cohorte, materia = await _crear_tenant_y_materia(db_session)
        usuario = await _crear_usuario(db_session, tenant.id)

        await _crear_fecha_service(db_session, tenant.id, usuario.id, materia.id, cohorte.id, tipo="Parcial", numero=1, fecha=date(2025, 10, 15), titulo="1er Parcial")
        await _crear_fecha_service(db_session, tenant.id, usuario.id, materia.id, cohorte.id, tipo="TP", numero=1, fecha=date(2025, 9, 1), titulo="TP 1")

        svc = GeneracionLMSService(db_session, tenant.id)
        result = await svc.generar_contenido_lms(materia.id, cohorte.id)

        assert result.cantidad_fechas == 2
        assert "<table" in result.html
        assert "1er Parcial" in result.html
        assert "TP 1" in result.html

    @pytest.mark.asyncio
    async def test_generar_lms_sin_fechas(self, db_session: AsyncSession):
        """GREEN: generar_contenido_lms sin fechas → mensaje."""
        from app.services.programa_materia_service import GeneracionLMSService

        tenant, carrera, cohorte, materia = await _crear_tenant_y_materia(db_session)

        svc = GeneracionLMSService(db_session, tenant.id)
        result = await svc.generar_contenido_lms(materia.id, cohorte.id)

        assert result.cantidad_fechas == 0
        assert "No hay fechas académicas" in result.html


# ---------------------------------------------------------------------------
# Grupo 5: Multi-tenancy
# ---------------------------------------------------------------------------


class TestMultiTenancy:
    """Task 6.3: aislamiento multi-tenant."""

    @pytest.mark.asyncio
    async def test_tenant_aislamiento_programa(self, db_session: AsyncSession):
        """RED: tenant A no ve programa de tenant B."""
        from app.services.programa_materia_service import ProgramaMateriaService

        tenant_a, carrera_a, cohorte_a, materia_a = await _crear_tenant_y_materia(db_session)
        tenant_b, carrera_b, cohorte_b, materia_b = await _crear_tenant_y_materia(db_session)

        usuario_a = await _crear_usuario(db_session, tenant_a.id, "a@test.com")
        usuario_b = await _crear_usuario(db_session, tenant_b.id, "b@test.com")

        svc_a = ProgramaMateriaService(db_session, tenant_a.id, usuario_a.id)
        created = await svc_a.crear_programa({
            "materia_id": materia_a.id,
            "carrera_id": carrera_a.id,
            "cohorte_id": cohorte_a.id,
            "titulo": "Programa A",
            "referencia_archivo": "s3://bucket/a.pdf",
        })

        svc_b = ProgramaMateriaService(db_session, tenant_b.id, usuario_b.id)
        with pytest.raises(HTTPException) as exc_info:
            await svc_b.get_programa(created.id)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Grupo 6: Permisos
# ---------------------------------------------------------------------------


class TestPermisos:
    """Task 6.6: tests de permisos en endpoints."""

    @pytest.fixture
    async def admin_token(self, db_session: AsyncSession, default_tenant):
        """Crea usuario con permiso estructura:gestionar."""
        from app.core import security
        from app.models.user import Usuario
        from app.repositories.rbac_repository import (
            RolRepository,
            PermisoRepository,
            RolPermisoRepository,
        )

        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        admin_rol = await rol_repo.create(codigo="ADMIN", nombre="Administrador")
        perm = await perm_repo.create(codigo="estructura:gestionar", nombre="Gestionar estructura", modulo="estructura")
        await rp_repo.create(rol_id=admin_rol.id, permiso_id=perm.id, es_propio=False)

        user = Usuario(
            nombre="Admin", apellidos="Test", email="admin@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = security.create_access_token(
            user_id=user.id,
            tenant_id=default_tenant.id,
            roles=["ADMIN"],
        )
        return token

    @pytest.fixture
    async def no_perms_token(self, db_session: AsyncSession, default_tenant):
        """Crea usuario sin permisos."""
        from app.core import security
        from app.models.user import Usuario
        from app.repositories.rbac_repository import RolRepository

        rol_repo = RolRepository(db_session, default_tenant.id)
        await rol_repo.create(codigo="NEXO", nombre="Nexo")

        user = Usuario(
            nombre="Nexo", apellidos="Test", email="nexo@test.com",
            estado="activo", tenant_id=default_tenant.id,
            password_hash=security.hash_password("Pass1234"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = security.create_access_token(
            user_id=user.id,
            tenant_id=default_tenant.id,
            roles=["NEXO"],
        )
        return token

    @pytest.mark.asyncio
    async def test_post_programa_sin_permiso(self, async_client, no_perms_token):
        """RED: POST sin permiso → 403."""
        from uuid import uuid4

        response = await async_client.post(
            "/api/programas/",
            json={
                "materia_id": str(uuid4()),
                "carrera_id": str(uuid4()),
                "cohorte_id": str(uuid4()),
                "titulo": "Programa",
                "referencia_archivo": "s3://bucket/programa.pdf",
            },
            headers={"Authorization": f"Bearer {no_perms_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_post_fecha_sin_permiso(self, async_client, no_perms_token):
        """RED: POST sin permiso → 403."""
        from uuid import uuid4

        response = await async_client.post(
            "/api/fechas-academicas/",
            json={
                "materia_id": str(uuid4()),
                "cohorte_id": str(uuid4()),
                "tipo": "Parcial",
                "numero": 1,
                "periodo": "2025-2",
                "fecha": "2025-10-15",
                "titulo": "1er Parcial",
            },
            headers={"Authorization": f"Bearer {no_perms_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_programas_con_permiso(self, async_client, admin_token, db_session: AsyncSession, default_tenant):
        """GREEN: GET con permiso → 200."""
        from app.models.estructura import Materia

        materia = Materia(
            tenant_id=default_tenant.id,
            codigo="PROG_I",
            nombre="Programación I",
            estado="Activa",
        )
        db_session.add(materia)
        await db_session.commit()
        await db_session.refresh(materia)

        response = await async_client.get(
            f"/api/programas/?materia_id={materia.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
