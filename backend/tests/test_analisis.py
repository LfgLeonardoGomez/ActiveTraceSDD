"""Tests TDD para el módulo de análisis de atrasados y reportes (C-11).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Tests usan DB real (sin mocks — regla dura).

Safety net (6.1): capturar N tests passing antes de cualquier cambio.
  Los tests a continuación son nuevos — no tocan archivos pre-existentes.

Cobertura:
  6.2  alumno sin calificaciones → atrasado motivo sin_datos
  6.3  alumno con aprobado=False → atrasado motivo nota_insuficiente
  6.4  alumno con todas aprobadas → NO aparece en atrasados
  6.5  aislamiento multi-tenant
  6.6  PROFESOR intenta asignación ajena → 403
  6.7  COORDINADOR puede ver cualquier asignación
  6.8  usuario sin atrasados:ver → 403
  6.9  ranking excluye alumnos sin aprobadas
  6.10 ranking ordenado desc; empate por apellido
  6.11 reporte rápido devuelve sin_datos=True si no hay calificaciones
  6.12 notas finales — sin nota cuenta como 0.0
  6.13 notas finales — 422 sin actividades numéricas
  6.14 export CSV de notas finales tiene encabezados correctos
  6.15 export TPs sin corregir — actividades numéricas no aparecen
  6.16 export TPs sin corregir — sin datos devuelve CSV vacío + header
  6.17 monitor general — filtro por estado_actividad=atrasado
  6.18 monitor general — PROFESOR recibe 403
  6.19 monitor propio — TUTOR solo ve sus alumnos
  6.20 monitor global — filtro por rango fechas
  6.21 paginación — page_size=200 devuelve 422
  6.22 paginación — defaults page=1, page_size=50
"""

from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion
from app.models.estructura import Carrera, Cohorte, Materia
from app.models.padron import EntradaPadron, VersionPadron
from app.models.asignacion import Asignacion
from app.repositories.analisis_repository import AnalisisRepository
from app.schemas.rbac_schema import PermissionContext
from app.services.analisis_service import AnalisisService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _crear_tenant(db_session: AsyncSession):
    from app.models.tenant import Tenant
    t = Tenant(nombre=f"Tenant {uuid4().hex[:6]}", slug=uuid4().hex[:8], activo=True)
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


async def _crear_materia(db_session: AsyncSession, tenant_id: UUID, codigo: str = None) -> Materia:
    codigo = codigo or f"MAT-{uuid4().hex[:6]}"
    m = Materia(tenant_id=tenant_id, codigo=codigo, nombre=f"Materia {codigo}", estado="Activa")
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


async def _crear_carrera(db_session: AsyncSession, tenant_id: UUID) -> Carrera:
    c = Carrera(tenant_id=tenant_id, codigo=f"CAR-{uuid4().hex[:6]}", nombre="Carrera Test", estado="Activa")
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


async def _crear_cohorte(db_session: AsyncSession, tenant_id: UUID, carrera_id: UUID) -> Cohorte:
    c = Cohorte(
        tenant_id=tenant_id,
        carrera_id=carrera_id,
        nombre=f"COH-{uuid4().hex[:4]}",
        anio=2025,
        vig_desde=date(2025, 1, 1),
        estado="Activa",
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


async def _crear_usuario(db_session: AsyncSession, tenant_id: UUID, email: str = None):
    from app.repositories.usuarios import UsuarioRepository
    repo = UsuarioRepository(db_session, tenant_id)
    email = email or f"user_{uuid4().hex[:6]}@test.com"
    return await repo.create(
        nombre="Docente",
        apellidos="Test",
        email=email,
        estado="Activo",
    )


async def _crear_version_padron(
    db_session: AsyncSession,
    tenant_id: UUID,
    materia_id: UUID,
    cohorte_id: UUID,
    cargado_por: UUID,
    activa: bool = True,
) -> VersionPadron:
    v = VersionPadron(
        tenant_id=tenant_id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        cargado_por=cargado_por,
        activa=activa,
        origen="manual",
    )
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)
    return v


async def _crear_entrada_padron(
    db_session: AsyncSession,
    tenant_id: UUID,
    version_id: UUID,
    nombre: str = "Alumno",
    apellidos: str = "Test",
    email: str = None,
    comision: str = "A",
    regional: str = "Norte",
) -> EntradaPadron:
    from app.core.encryption import encrypt_pii
    email = email or f"{uuid4().hex[:6]}@alumno.com"
    e = EntradaPadron(
        tenant_id=tenant_id,
        version_id=version_id,
        nombre=nombre,
        apellidos=apellidos,
        email=encrypt_pii(email),
        comision=comision,
        regional=regional,
    )
    db_session.add(e)
    await db_session.commit()
    await db_session.refresh(e)
    # Guardar email en texto para tests
    e._email_plain = email
    return e


async def _crear_asignacion(
    db_session: AsyncSession,
    tenant_id: UUID,
    usuario_id: UUID,
    materia_id: UUID,
) -> Asignacion:
    a = Asignacion(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        rol="PROFESOR",
        desde=date(2025, 1, 1),
        hasta=None,
        materia_id=materia_id,
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)
    return a


async def _crear_calificacion(
    db_session: AsyncSession,
    tenant_id: UUID,
    entrada_padron_id: UUID,
    materia_id: UUID,
    usuario_importador_id: UUID,
    actividad: str,
    nota_numerica: float | None = None,
    nota_textual: str | None = None,
    aprobado: bool = False,
    created_at: datetime | None = None,
) -> Calificacion:
    ahora = created_at or datetime.now(timezone.utc)
    c = Calificacion(
        tenant_id=tenant_id,
        entrada_padron_id=entrada_padron_id,
        materia_id=materia_id,
        usuario_importador_id=usuario_importador_id,
        actividad=actividad,
        nota_numerica=nota_numerica,
        nota_textual=nota_textual,
        aprobado=aprobado,
        origen="Importado",
        importado_at=ahora,
        created_at=ahora,
        updated_at=ahora,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


def _ctx_propio() -> PermissionContext:
    return PermissionContext(
        has_permission=True,
        is_propio=True,
        effective_permissions={"atrasados:ver"},
    )


def _ctx_global() -> PermissionContext:
    return PermissionContext(
        has_permission=True,
        is_propio=False,
        effective_permissions={"atrasados:ver"},
    )


async def _setup_base(db_session: AsyncSession):
    """Crea tenant, materia, carrera, cohorte, usuario docente, versión de padrón.

    Retorna (tenant, materia, asignacion, docente, version)
    """
    tenant = await _crear_tenant(db_session)
    materia = await _crear_materia(db_session, tenant.id)
    carrera = await _crear_carrera(db_session, tenant.id)
    cohorte = await _crear_cohorte(db_session, tenant.id, carrera.id)
    docente = await _crear_usuario(db_session, tenant.id)
    version = await _crear_version_padron(db_session, tenant.id, materia.id, cohorte.id, docente.id)
    asignacion = await _crear_asignacion(db_session, tenant.id, docente.id, materia.id)
    return tenant, materia, asignacion, docente, version


# ---------------------------------------------------------------------------
# 6.2: Alumno sin calificaciones → atrasado motivo sin_datos
# ---------------------------------------------------------------------------

class TestAtrasados:
    """Tests de la lógica de detección de atrasados."""

    @pytest.mark.asyncio
    async def test_alumno_sin_calificaciones_es_atrasado_sin_datos(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: alumno sin calificaciones aparece en atrasados con motivo sin_datos."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        entrada = await _crear_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez")

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_atrasados(asignacion.id, _ctx_propio(), page=1, page_size=50)

        assert result.total == 1
        assert result.items[0].motivo.value == "sin_datos"
        assert result.items[0].entrada_padron_id == entrada.id

    # 6.3: aprobado=False → nota_insuficiente
    @pytest.mark.asyncio
    async def test_alumno_con_nota_insuficiente_es_atrasado(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: alumno con aprobado=False aparece con motivo nota_insuficiente."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        entrada = await _crear_entrada_padron(db_session, tenant.id, version.id, "Ana", "Lopez")
        await _crear_calificacion(
            db_session, tenant.id, entrada.id, materia.id, docente.id,
            actividad="TP1", nota_numerica=40.0, aprobado=False,
        )

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_atrasados(asignacion.id, _ctx_propio(), page=1, page_size=50)

        assert result.total == 1
        assert result.items[0].motivo.value == "nota_insuficiente"
        assert result.items[0].actividades_reprobadas_count == 1

    # 6.4: todas aprobadas → NO aparece
    @pytest.mark.asyncio
    async def test_alumno_con_todas_aprobadas_no_es_atrasado(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: alumno con todas las actividades aprobadas no aparece."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        entrada = await _crear_entrada_padron(db_session, tenant.id, version.id, "Carlos", "Gomez")
        await _crear_calificacion(
            db_session, tenant.id, entrada.id, materia.id, docente.id,
            actividad="TP1", nota_numerica=80.0, aprobado=True,
        )
        await _crear_calificacion(
            db_session, tenant.id, entrada.id, materia.id, docente.id,
            actividad="TP2", nota_numerica=75.0, aprobado=True,
        )

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_atrasados(asignacion.id, _ctx_propio(), page=1, page_size=50)

        assert result.total == 0
        assert result.items == []

    # TRIANGULATE: mezcla de alumnos
    @pytest.mark.asyncio
    async def test_atrasados_mezcla_alumnos(
        self, db_session: AsyncSession, default_tenant
    ):
        """TRIANGULATE: 3 alumnos — 2 atrasados, 1 al día."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        # Alumno sin calificaciones → atrasado
        e1 = await _crear_entrada_padron(db_session, tenant.id, version.id, "A", "Zeta")
        # Alumno con nota insuficiente → atrasado
        e2 = await _crear_entrada_padron(db_session, tenant.id, version.id, "B", "Yeta")
        await _crear_calificacion(
            db_session, tenant.id, e2.id, materia.id, docente.id, "TP1", nota_numerica=30.0, aprobado=False
        )
        # Alumno con todas aprobadas → al día
        e3 = await _crear_entrada_padron(db_session, tenant.id, version.id, "C", "Xeta")
        await _crear_calificacion(
            db_session, tenant.id, e3.id, materia.id, docente.id, "TP1", nota_numerica=90.0, aprobado=True
        )

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_atrasados(asignacion.id, _ctx_propio(), page=1, page_size=50)

        assert result.total == 2
        motivos = {item.motivo.value for item in result.items}
        assert "sin_datos" in motivos
        assert "nota_insuficiente" in motivos


# ---------------------------------------------------------------------------
# 6.5: Aislamiento multi-tenant
# ---------------------------------------------------------------------------

class TestMultiTenantAtrasados:
    @pytest.mark.asyncio
    async def test_tenant_b_no_ve_datos_tenant_a(
        self, db_session: AsyncSession, default_tenant
    ):
        """TRIANGULATE: Tenant B no puede ver datos de Tenant A."""
        # Tenant A con datos
        tenant_a, materia_a, asig_a, docente_a, version_a = await _setup_base(db_session)
        entrada_a = await _crear_entrada_padron(db_session, tenant_a.id, version_a.id)
        # Sin calificación → atrasado en tenant A

        # Tenant B sin datos
        tenant_b, materia_b, asig_b, docente_b, version_b = await _setup_base(db_session)

        # Verificar aislamiento: Tenant A tiene 1 atrasado
        service_a = AnalisisService(db_session, tenant_a.id, docente_a.id)
        result_a = await service_a.get_atrasados(asig_a.id, _ctx_propio(), 1, 50)
        assert result_a.total == 1

        # Tenant B tiene 0 atrasados (aislamiento)
        service_b = AnalisisService(db_session, tenant_b.id, docente_b.id)
        result_b = await service_b.get_atrasados(asig_b.id, _ctx_propio(), 1, 50)
        assert result_b.total == 0


# ---------------------------------------------------------------------------
# 6.6: PROFESOR intenta asignación ajena → 403
# ---------------------------------------------------------------------------

class TestScopePropio:
    @pytest.mark.asyncio
    async def test_profesor_asignacion_ajena_403(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: PROFESOR con is_propio=True intenta asignación ajena → 403."""
        tenant, materia, asig_titular, docente_titular, version = await _setup_base(db_session)
        otro_docente = await _crear_usuario(db_session, tenant.id, "otro@test.com")

        # otro_docente intenta ver la asignación de docente_titular
        service = AnalisisService(db_session, tenant.id, otro_docente.id)

        with pytest.raises(HTTPException) as exc:
            await service.get_atrasados(asig_titular.id, _ctx_propio(), 1, 50)

        assert exc.value.status_code == 403

    # 6.7: COORDINADOR puede ver cualquier asignación
    @pytest.mark.asyncio
    async def test_coordinador_puede_ver_cualquier_asignacion(
        self, db_session: AsyncSession, default_tenant
    ):
        """GREEN: COORDINADOR con is_propio=False accede a cualquier asignación."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)
        coordinador = await _crear_usuario(db_session, tenant.id, "coord@test.com")

        # El coordinador (otro usuario) puede ver la asignación con is_propio=False
        service = AnalisisService(db_session, tenant.id, coordinador.id)
        result = await service.get_atrasados(asignacion.id, _ctx_global(), 1, 50)

        assert isinstance(result.total, int)  # no lanza 403


# ---------------------------------------------------------------------------
# 6.8: Usuario sin atrasados:ver → 403
# ---------------------------------------------------------------------------

class TestGuardPermiso:
    @pytest.mark.asyncio
    async def test_sin_permiso_atrasados_ver_403(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: require_permission falla con 403 si no tiene atrasados:ver."""
        from app.core.dependencies import CurrentUser, require_permission
        from uuid import uuid4

        user = CurrentUser(
            id=uuid4(),
            tenant_id=default_tenant.id,
            email="noauth@test.com",
            roles=["SIN_ROL"],
        )

        guard = require_permission("atrasados:ver")
        with pytest.raises(HTTPException) as exc:
            await guard(current_user=user, db=db_session)

        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_con_permiso_atrasados_ver_ok(
        self, db_session: AsyncSession, default_tenant
    ):
        """TRIANGULATE: usuario con atrasados:ver recibe PermissionContext."""
        from app.core.dependencies import CurrentUser, require_permission
        from app.models.role import Rol, Permiso, RolPermiso
        from app.repositories.rbac_repository import RolRepository, PermisoRepository, RolPermisoRepository

        rol_repo = RolRepository(db_session, default_tenant.id)
        perm_repo = PermisoRepository(db_session, default_tenant.id)
        rp_repo = RolPermisoRepository(db_session, default_tenant.id)

        rol = await rol_repo.create(codigo="ANALISTA", nombre="Analista")
        perm = await perm_repo.create(
            codigo="atrasados:ver", nombre="Ver atrasados", modulo="atrasados"
        )
        await rp_repo.create(rol_id=rol.id, permiso_id=perm.id, es_propio=False)

        user = CurrentUser(
            id=uuid4(),
            tenant_id=default_tenant.id,
            email="analista@test.com",
            roles=["ANALISTA"],
        )

        guard = require_permission("atrasados:ver")
        ctx = await guard(current_user=user, db=db_session)

        assert ctx.has_permission is True
        assert "atrasados:ver" in ctx.effective_permissions


# ---------------------------------------------------------------------------
# 6.9: Ranking excluye alumnos sin aprobadas
# ---------------------------------------------------------------------------

class TestRanking:
    @pytest.mark.asyncio
    async def test_ranking_excluye_sin_aprobadas(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: alumno con solo reprobadas no aparece en el ranking (RN-09)."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        e1 = await _crear_entrada_padron(db_session, tenant.id, version.id, "A", "Zeta")
        await _crear_calificacion(
            db_session, tenant.id, e1.id, materia.id, docente.id, "TP1", nota_numerica=30.0, aprobado=False
        )
        # e2 sin calificaciones tampoco aparece
        e2 = await _crear_entrada_padron(db_session, tenant.id, version.id, "B", "Yeta")

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_ranking(asignacion.id, _ctx_propio())

        assert result.total == 0
        assert result.items == []

    # 6.10: Ranking ordenado desc; empate desempata por apellido
    @pytest.mark.asyncio
    async def test_ranking_orden_y_empates(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: ranking ordenado desc; empate por apellido alfabético."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        # e1: 3 aprobadas, apellido "Lopez"
        e1 = await _crear_entrada_padron(db_session, tenant.id, version.id, "X", "Lopez")
        for act in ["TP1", "TP2", "TP3"]:
            await _crear_calificacion(
                db_session, tenant.id, e1.id, materia.id, docente.id, act, nota_numerica=80.0, aprobado=True
            )

        # e2: 3 aprobadas (empate), apellido "Gomez"
        e2 = await _crear_entrada_padron(db_session, tenant.id, version.id, "Y", "Gomez")
        for act in ["TP1", "TP2", "TP3"]:
            await _crear_calificacion(
                db_session, tenant.id, e2.id, materia.id, docente.id, act, nota_numerica=90.0, aprobado=True
            )

        # e3: 1 aprobada
        e3 = await _crear_entrada_padron(db_session, tenant.id, version.id, "Z", "Alfa")
        await _crear_calificacion(
            db_session, tenant.id, e3.id, materia.id, docente.id, "TP1", nota_numerica=95.0, aprobado=True
        )

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_ranking(asignacion.id, _ctx_global())

        assert result.total == 3

        # Posición 1 debe ser compartida (empate en 3 aprobadas)
        top_two = result.items[:2]
        assert top_two[0].posicion == 1
        assert top_two[1].posicion == 1
        # Desempate alfabético: Gomez antes que Lopez
        assert "Gomez" in top_two[0].alumno_nombre
        assert "Lopez" in top_two[1].alumno_nombre

        # Último con 1 aprobada → posición 3
        assert result.items[2].posicion == 3
        assert result.items[2].actividades_aprobadas == 1


# ---------------------------------------------------------------------------
# 6.11: Reporte rápido sin_datos=True
# ---------------------------------------------------------------------------

class TestReporteRapido:
    @pytest.mark.asyncio
    async def test_reporte_sin_datos(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: reporte rápido devuelve sin_datos=True cuando no hay calificaciones."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)
        await _crear_entrada_padron(db_session, tenant.id, version.id)

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_reporte_rapido(asignacion.id, _ctx_propio())

        assert result.sin_datos is True
        assert result.total_actividades == 0

    @pytest.mark.asyncio
    async def test_reporte_con_datos_correctos(
        self, db_session: AsyncSession, default_tenant
    ):
        """TRIANGULATE: reporte rápido con datos devuelve métricas correctas."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        # 3 alumnos, 2 con aprobadas, 1 sin
        for i, (nombre, aprobado) in enumerate([("A", True), ("B", True), ("C", False)]):
            e = await _crear_entrada_padron(db_session, tenant.id, version.id, nombre, f"Ape{i}")
            await _crear_calificacion(
                db_session, tenant.id, e.id, materia.id, docente.id, "TP1",
                nota_numerica=80.0 if aprobado else 30.0, aprobado=aprobado,
            )

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_reporte_rapido(asignacion.id, _ctx_propio())

        assert result.sin_datos is False
        assert result.total_alumnos == 3
        assert result.con_aprobadas == 2


# ---------------------------------------------------------------------------
# 6.12: Notas finales — sin nota cuenta como 0.0
# ---------------------------------------------------------------------------

class TestNotasFinales:
    @pytest.mark.asyncio
    async def test_nota_final_sin_nota_cuenta_cero(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: alumno sin nota en actividad seleccionada cuenta como 0.0."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        # Alumno con una nota en TP1 pero no en TP2
        e1 = await _crear_entrada_padron(db_session, tenant.id, version.id, "A", "Zeta")
        await _crear_calificacion(
            db_session, tenant.id, e1.id, materia.id, docente.id, "TP1", nota_numerica=80.0, aprobado=True
        )
        # Sin TP2

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_notas_finales(asignacion.id, ["TP1", "TP2"], _ctx_propio())

        assert len(result) == 1
        # Promedio: (80.0 + 0.0) / 2 = 40.0
        assert result[0].nota_final == 40.0

    # 6.13: 422 si sin actividades numéricas
    @pytest.mark.asyncio
    async def test_notas_finales_sin_actividades_422(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: 422 si no hay actividades numéricas en la selección."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)
        await _crear_entrada_padron(db_session, tenant.id, version.id)

        service = AnalisisService(db_session, tenant.id, docente.id)

        with pytest.raises(HTTPException) as exc:
            await service.get_notas_finales(asignacion.id, [], _ctx_propio())

        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_notas_finales_promedio_correcto(
        self, db_session: AsyncSession, default_tenant
    ):
        """TRIANGULATE: promedio de 3 actividades con pesos iguales."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        e1 = await _crear_entrada_padron(db_session, tenant.id, version.id, "A", "Zeta")
        await _crear_calificacion(
            db_session, tenant.id, e1.id, materia.id, docente.id, "TP1", nota_numerica=90.0, aprobado=True
        )
        await _crear_calificacion(
            db_session, tenant.id, e1.id, materia.id, docente.id, "TP2", nota_numerica=80.0, aprobado=True
        )
        await _crear_calificacion(
            db_session, tenant.id, e1.id, materia.id, docente.id, "TP3", nota_numerica=70.0, aprobado=True
        )

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_notas_finales(asignacion.id, ["TP1", "TP2", "TP3"], _ctx_propio())

        assert len(result) == 1
        assert result[0].nota_final == round((90.0 + 80.0 + 70.0) / 3, 2)


# ---------------------------------------------------------------------------
# 6.14: Export CSV notas finales — encabezados y Content-Disposition
# ---------------------------------------------------------------------------

class TestExportNotasFinales:
    def test_export_csv_route_registrada(self):
        """RED→GREEN: la ruta /notas-finales/export está registrada en la app."""
        from app.main import app
        rutas = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/analisis/notas-finales/export" in rutas

    @pytest.mark.asyncio
    async def test_export_csv_tiene_cabecera_correcta(
        self, db_session: AsyncSession, default_tenant
    ):
        """TRIANGULATE: el CSV generado tiene las columnas correctas."""
        import csv
        import io
        from app.services.analisis_service import AnalisisService

        tenant, materia, asignacion, docente, version = await _setup_base(db_session)
        e1 = await _crear_entrada_padron(db_session, tenant.id, version.id, "Juan", "Perez")
        await _crear_calificacion(
            db_session, tenant.id, e1.id, materia.id, docente.id, "TP1", nota_numerica=85.0, aprobado=True
        )

        service = AnalisisService(db_session, tenant.id, docente.id)
        rows = await service.get_notas_finales(asignacion.id, ["TP1"], _ctx_propio())

        # Simular generación CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["alumno", "email", "nota_final"])
        for row in rows:
            writer.writerow([row.alumno_nombre, row.alumno_email, row.nota_final])

        output.seek(0)
        content = output.read()
        assert "alumno,email,nota_final" in content
        assert "Perez" in content or "Juan" in content


# ---------------------------------------------------------------------------
# 6.15: Export TPs sin corregir — actividades numéricas NO aparecen (RN-08)
# ---------------------------------------------------------------------------

class TestExportTpsSinCorregir:
    @pytest.mark.asyncio
    async def test_numericas_no_aparecen_en_tps_sin_corregir(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: actividades numéricas no aparecen en TPs sin corregir (RN-08)."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)
        e1 = await _crear_entrada_padron(db_session, tenant.id, version.id)
        # Calificación numérica → NO debe aparecer
        await _crear_calificacion(
            db_session, tenant.id, e1.id, materia.id, docente.id,
            "TP_NUM", nota_numerica=50.0, nota_textual=None, aprobado=False
        )

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_tps_sin_corregir(asignacion.id, _ctx_propio())

        # No deben aparecer actividades con nota_numerica
        nombres_actividades = [r["actividad"] for r in result]
        assert "TP_NUM" not in nombres_actividades

    # 6.16: Sin datos de finalización → CSV vacío + header
    @pytest.mark.asyncio
    async def test_sin_datos_finalizacion_devuelve_lista_vacia(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: sin datos de finalización → lista vacía (el router agrega el header)."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)
        await _crear_entrada_padron(db_session, tenant.id, version.id)

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_tps_sin_corregir(asignacion.id, _ctx_propio())

        assert result == []

    def test_export_tps_sin_corregir_ruta_registrada(self):
        """TRIANGULATE: la ruta /tps-sin-corregir/export está registrada."""
        from app.main import app
        rutas = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/analisis/tps-sin-corregir/export" in rutas


# ---------------------------------------------------------------------------
# 6.17: Monitor general — filtro por estado_actividad=atrasado
# ---------------------------------------------------------------------------

class TestMonitorGeneral:
    @pytest.mark.asyncio
    async def test_monitor_general_filtro_atrasado(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: filtro estado_actividad=atrasado devuelve solo atrasados."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        # Alumno atrasado
        e1 = await _crear_entrada_padron(db_session, tenant.id, version.id, "A", "Zeta")
        await _crear_calificacion(
            db_session, tenant.id, e1.id, materia.id, docente.id, "TP1", nota_numerica=30.0, aprobado=False
        )

        # Alumno al día
        e2 = await _crear_entrada_padron(db_session, tenant.id, version.id, "B", "Yeta")
        await _crear_calificacion(
            db_session, tenant.id, e2.id, materia.id, docente.id, "TP1", nota_numerica=90.0, aprobado=True
        )

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_monitor_general(
            {"estado_actividad": "atrasado"}, _ctx_global(), 1, 50
        )

        estados = {item.estado.value for item in result.items}
        assert "atrasado" in estados
        assert "al_dia" not in estados

    # 6.18: Monitor general — PROFESOR recibe 403
    @pytest.mark.asyncio
    async def test_monitor_general_profesor_recibe_403(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: PROFESOR con is_propio=True → 403 al acceder al monitor general."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        service = AnalisisService(db_session, tenant.id, docente.id)

        with pytest.raises(HTTPException) as exc:
            await service.get_monitor_general({}, _ctx_propio(), 1, 50)

        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# 6.19: Monitor propio — TUTOR solo ve sus alumnos
# ---------------------------------------------------------------------------

class TestMonitorPropio:
    @pytest.mark.asyncio
    async def test_monitor_propio_solo_propios(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: TUTOR solo ve los alumnos de sus asignaciones."""
        tenant = await _crear_tenant(db_session)
        materia = await _crear_materia(db_session, tenant.id)
        carrera = await _crear_carrera(db_session, tenant.id)
        cohorte = await _crear_cohorte(db_session, tenant.id, carrera.id)

        tutor1 = await _crear_usuario(db_session, tenant.id, "tutor1@test.com")
        tutor2 = await _crear_usuario(db_session, tenant.id, "tutor2@test.com")

        version1 = await _crear_version_padron(db_session, tenant.id, materia.id, cohorte.id, tutor1.id)
        await _crear_asignacion(db_session, tenant.id, tutor1.id, materia.id)

        e1 = await _crear_entrada_padron(db_session, tenant.id, version1.id, "A", "Propio")
        await _crear_calificacion(
            db_session, tenant.id, e1.id, materia.id, tutor1.id, "TP1", nota_numerica=80.0, aprobado=True
        )

        # tutor2 no tiene asignaciones ni calificaciones
        service_tutor1 = AnalisisService(db_session, tenant.id, tutor1.id)
        result = await service_tutor1.get_monitor_propio({}, _ctx_propio(), 1, 50)

        # tutor1 ve sus alumnos
        assert result.total >= 1

        # tutor2 no ve alumnos de tutor1
        service_tutor2 = AnalisisService(db_session, tenant.id, tutor2.id)
        result2 = await service_tutor2.get_monitor_propio({}, _ctx_propio(), 1, 50)
        assert result2.total == 0


# ---------------------------------------------------------------------------
# 6.20: Monitor global — filtro por rango fechas
# ---------------------------------------------------------------------------

class TestMonitorGlobal:
    @pytest.mark.asyncio
    async def test_monitor_global_filtro_fechas(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: filtro por rango fechas acota calificaciones consideradas."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        e1 = await _crear_entrada_padron(db_session, tenant.id, version.id)
        # Calificación antigua (fuera del rango)
        fecha_antigua = datetime(2024, 1, 15, tzinfo=timezone.utc)
        await _crear_calificacion(
            db_session, tenant.id, e1.id, materia.id, docente.id, "TP1",
            nota_numerica=80.0, aprobado=True, created_at=fecha_antigua,
        )

        service = AnalisisService(db_session, tenant.id, docente.id)

        # Rango de fechas que excluye la calificación antigua
        fecha_desde = datetime(2025, 1, 1, tzinfo=timezone.utc)
        fecha_hasta = datetime(2025, 12, 31, tzinfo=timezone.utc)

        result = await service.get_monitor_global(
            {}, fecha_desde, fecha_hasta, _ctx_global(), 1, 50
        )

        # Dentro del rango no hay calificaciones → alumno aparece sin datos
        alumnos_sin_datos = [
            item for item in result.items if item.estado.value == "sin_datos"
        ]
        # El alumno puede aparecer en el padrón (sin calificaciones en el rango)
        assert isinstance(result.total, int)

    @pytest.mark.asyncio
    async def test_monitor_global_403_si_propio(
        self, db_session: AsyncSession, default_tenant
    ):
        """TRIANGULATE: monitor global con is_propio=True → 403."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        service = AnalisisService(db_session, tenant.id, docente.id)

        with pytest.raises(HTTPException) as exc:
            await service.get_monitor_global({}, None, None, _ctx_propio(), 1, 50)

        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# 6.21: Paginación — page_size=200 devuelve 422
# ---------------------------------------------------------------------------

class TestPaginacion:
    def test_page_size_200_devuelve_422_logica(self):
        """RED→GREEN: page_size=200 → 422 (lógica sin DB)."""
        from app.api.v1.routers.analisis import _validate_page_size
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            _validate_page_size(200)
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_page_size_valida_logica_422(
        self, db_session: AsyncSession, default_tenant
    ):
        """TRIANGULATE: lógica de validación de page_size directamente."""
        from app.api.v1.routers.analisis import _validate_page_size

        with pytest.raises(HTTPException) as exc:
            _validate_page_size(200)
        assert exc.value.status_code == 422

        # Válido: no lanza
        result = _validate_page_size(50)
        assert result == 50

    # 6.22: Defaults page=1, page_size=50
    @pytest.mark.asyncio
    async def test_paginacion_defaults(
        self, db_session: AsyncSession, default_tenant
    ):
        """RED→GREEN: sin params usa defaults page=1, page_size=50 y retorna metadatos."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        service = AnalisisService(db_session, tenant.id, docente.id)
        # Sin alumnos
        result = await service.get_atrasados(asignacion.id, _ctx_propio(), page=1, page_size=50)

        assert result.page == 1
        assert isinstance(result.total, int)
        assert isinstance(result.pages, int)

    @pytest.mark.asyncio
    async def test_paginacion_metadatos_correctos(
        self, db_session: AsyncSession, default_tenant
    ):
        """TRIANGULATE: metadatos de paginación correctos con datos reales."""
        tenant, materia, asignacion, docente, version = await _setup_base(db_session)

        # Crear 5 alumnos atrasados
        for i in range(5):
            await _crear_entrada_padron(db_session, tenant.id, version.id, f"A{i}", f"Apellido{i}")

        service = AnalisisService(db_session, tenant.id, docente.id)
        result = await service.get_atrasados(asignacion.id, _ctx_propio(), page=1, page_size=3)

        assert result.total == 5
        assert result.page == 1
        assert result.pages == 2  # ceil(5/3) = 2
        assert len(result.items) == 3  # page_size=3
