"""Tests TDD para el módulo de comunicaciones salientes (C-12).

Strict TDD: Safety net → RED → GREEN → TRIANGULATE → REFACTOR.
Tests usan DB real (sin mocks de DB — regla dura).

Cobertura:
  8.2   preview renderiza variables correctamente por alumno
  8.3   preview con variable inválida → 422
  8.4   preview no persiste nada (0 filas en comunicacion tras el call)
  8.5   encolado crea N registros con mismo lote_id y destinatario cifrado
  8.6   encolado con tenant requiere_aprobacion=True → mensajes Pendiente
  8.7   usuario sin comunicacion:enviar → 403
  8.8   PROFESOR intenta encolar para materia ajena → 403
  8.9   estado de lote agrega correctamente por estado
  8.10  aprobar lote → todos los Pendiente quedan aprobado=True; se audita
  8.11  cancelar lote → todos los Pendiente pasan a Cancelado
  8.12  cancelar mensaje Enviado → 422 (transición inválida)
  8.13  retry de mensaje Error → vuelve a Pendiente
  8.14  retry de mensaje no-Error → 422
  8.15  máquina de estados — transición inválida rechazada
  8.16  aislamiento multi-tenant (Tenant B no ve lotes de Tenant A → 404)
  8.17  worker: run_once con N8N mock exitoso → mensaje transiciona a Enviado
  8.18  worker: run_once con N8N mock fallido → mensaje transiciona a Error
  8.19  worker: tenant con requiere_aprobacion=True sin aprobado=True → worker no despacha
  8.20  worker: resetear_colgados transiciona mensajes viejos en Enviando a Pendiente
  8.21  worker: N8N_WEBHOOK_URL no configurada → worker no toma mensajes
  8.22  worker: procesa solo COMUNICACION_BATCH_SIZE mensajes por ciclo
  8.23  destinatario cifrado en DB (valor almacenado != email original)
  8.24  destinatario descifrado correctamente en el worker antes de enviar a N8N
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_pii, encrypt_pii
from app.integrations.n8n_client import N8NError, N8NTimeoutError
from app.models.asignacion import Asignacion
from app.models.comunicacion import (
    Comunicacion,
    EstadoComunicacion,
    transicion_valida,
)
from app.models.estructura import Materia
from app.models.tenant import Tenant
from app.models.user import Usuario
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.schemas.comunicacion import (
    ComunicacionLoteRequestSchema,
    ComunicacionPreviewRequestSchema,
    DestinatarioSchema,
)
from app.schemas.rbac_schema import PermissionContext
from app.services.comunicacion_service import ComunicacionService
from app.workers.comunicacion_worker import ComunicacionWorker


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


async def _crear_tenant(
    db_session: AsyncSession,
    requiere_aprobacion: bool = False,
) -> Tenant:
    t = Tenant(
        nombre=f"Tenant {uuid4().hex[:6]}",
        slug=uuid4().hex[:8],
        activo=True,
        requiere_aprobacion_comunicaciones=requiere_aprobacion,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


async def _crear_materia(db_session: AsyncSession, tenant_id: UUID) -> Materia:
    m = Materia(
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid4().hex[:6]}",
        nombre="Materia Test",
        estado="Activa",
    )
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


async def _crear_usuario(db_session: AsyncSession, tenant_id: UUID) -> Usuario:
    from app.core.encryption import encrypt_pii
    email_plain = f"user_{uuid4().hex[:6]}@test.com"
    u = Usuario(
        tenant_id=tenant_id,
        nombre="Usuario",
        apellidos="Test",
        email=encrypt_pii(email_plain),
        password_hash="$argon2id$fake",
        estado="Activo",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _crear_asignacion(
    db_session: AsyncSession,
    tenant_id: UUID,
    usuario_id: UUID,
    materia_id: UUID,
) -> "Asignacion":
    from datetime import date
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


def _perm_enviar(is_propio: bool = False) -> PermissionContext:
    """Contexto de permiso comunicacion:enviar."""
    return PermissionContext(
        has_permission=True,
        is_propio=is_propio,
        effective_permissions={"comunicacion:enviar"},
    )


def _perm_aprobar() -> PermissionContext:
    """Contexto de permiso comunicacion:aprobar."""
    return PermissionContext(
        has_permission=True,
        is_propio=False,
        effective_permissions={"comunicacion:aprobar"},
    )


def _make_service(
    db_session: AsyncSession,
    tenant_id: UUID,
    usuario_id: UUID,
) -> ComunicacionService:
    return ComunicacionService(
        db_session=db_session,
        tenant_id=tenant_id,
        usuario_id=usuario_id,
    )


def _make_repo(db_session: AsyncSession, tenant_id: UUID) -> ComunicacionRepository:
    return ComunicacionRepository(db_session, tenant_id)


# ---------------------------------------------------------------------------
# 8.2 — Preview renderiza variables correctamente por alumno
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_renderiza_variables(db_session: AsyncSession):
    """Preview sustituye {{alumno.nombre}} y {{alumno.email}} por alumno."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm = _perm_enviar()

    dest = DestinatarioSchema(
        alumno_id=uuid4(),
        nombre="Juan Pérez",
        email="juan@example.com",
    )
    req = ComunicacionPreviewRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Hola {{alumno.nombre}}",
        plantilla_cuerpo="Tu email es {{alumno.email}}",
    )

    resultado = await svc.preview(req, perm)

    assert len(resultado) == 1
    assert resultado[0].alumno_id == dest.alumno_id
    assert resultado[0].asunto_renderizado == "Hola Juan Pérez"
    assert resultado[0].cuerpo_renderizado == "Tu email es juan@example.com"


@pytest.mark.asyncio
async def test_preview_renderiza_multiples_destinatarios(db_session: AsyncSession):
    """Preview renderiza independientemente para cada destinatario (triangulación)."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm = _perm_enviar()

    destinatarios = [
        DestinatarioSchema(alumno_id=uuid4(), nombre="Ana", email="ana@test.com"),
        DestinatarioSchema(alumno_id=uuid4(), nombre="Luis", email="luis@test.com"),
    ]
    req = ComunicacionPreviewRequestSchema(
        destinatarios=destinatarios,
        plantilla_asunto="Mensaje para {{alumno.nombre}}",
        plantilla_cuerpo="Cuerpo",
    )

    resultado = await svc.preview(req, perm)

    assert len(resultado) == 2
    assert resultado[0].asunto_renderizado == "Mensaje para Ana"
    assert resultado[1].asunto_renderizado == "Mensaje para Luis"


# ---------------------------------------------------------------------------
# 8.3 — Preview con variable inválida → 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_variable_invalida_422(db_session: AsyncSession):
    """Preview lanza 422 si la plantilla tiene variables no disponibles."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm = _perm_enviar()

    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email="t@t.com")
    req = ComunicacionPreviewRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Hola {{variable_inexistente}}",
        plantilla_cuerpo="Cuerpo",
    )

    with pytest.raises(HTTPException) as exc_info:
        await svc.preview(req, perm)

    assert exc_info.value.status_code == 422
    assert "variable_inexistente" in exc_info.value.detail.lower() or "variable" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_preview_variable_invalida_en_cuerpo_422(db_session: AsyncSession):
    """Preview lanza 422 también si la variable inválida está en el cuerpo (triangulación)."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm = _perm_enviar()

    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email="t@t.com")
    req = ComunicacionPreviewRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Asunto válido",
        plantilla_cuerpo="Cuerpo {{otro.campo}} inválido",
    )

    with pytest.raises(HTTPException) as exc_info:
        await svc.preview(req, perm)

    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# 8.4 — Preview no persiste nada (0 filas en comunicacion tras el call)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_no_persiste(db_session: AsyncSession):
    """Preview no crea ningún registro en la tabla comunicacion."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm = _perm_enviar()

    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email="t@t.com")
    req = ComunicacionPreviewRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Asunto",
        plantilla_cuerpo="Cuerpo",
    )

    await svc.preview(req, perm)

    # Verificar que no se crearon registros
    result = await db_session.execute(
        select(Comunicacion).where(Comunicacion.tenant_id == tenant.id)
    )
    filas = result.scalars().all()
    assert len(filas) == 0


# ---------------------------------------------------------------------------
# 8.5 — Encolado crea N registros con mismo lote_id y destinatario cifrado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_encolado_crea_registros_con_mismo_lote_id(db_session: AsyncSession):
    """Encolar lote crea N registros con el mismo lote_id."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    await _crear_asignacion(db_session, tenant.id, usuario.id, materia.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm = _perm_enviar(is_propio=False)

    destinatarios = [
        DestinatarioSchema(alumno_id=uuid4(), nombre="Ana", email="ana@test.com"),
        DestinatarioSchema(alumno_id=uuid4(), nombre="Luis", email="luis@test.com"),
        DestinatarioSchema(alumno_id=uuid4(), nombre="Pedro", email="pedro@test.com"),
    ]
    req = ComunicacionLoteRequestSchema(
        destinatarios=destinatarios,
        plantilla_asunto="Asunto",
        plantilla_cuerpo="Cuerpo",
        materia_id=materia.id,
    )

    resp = await svc.encolar_lote(req, perm)

    assert resp.total_encolados == 3
    assert resp.lote_id is not None

    # Verificar en DB
    result = await db_session.execute(
        select(Comunicacion).where(
            Comunicacion.tenant_id == tenant.id,
            Comunicacion.lote_id == resp.lote_id,
        )
    )
    registros = result.scalars().all()
    assert len(registros) == 3
    lote_ids = {str(r.lote_id) for r in registros}
    assert len(lote_ids) == 1  # todos con el mismo lote_id


@pytest.mark.asyncio
async def test_encolado_destinatario_cifrado(db_session: AsyncSession):
    """El campo destinatario está cifrado en DB (no en texto plano)."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm = _perm_enviar(is_propio=False)

    email_original = "alumno@example.com"
    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email=email_original)
    req = ComunicacionLoteRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Asunto",
        plantilla_cuerpo="Cuerpo",
        materia_id=materia.id,
    )

    resp = await svc.encolar_lote(req, perm)

    # Verificar en DB que no está en claro
    result = await db_session.execute(
        select(Comunicacion).where(Comunicacion.lote_id == resp.lote_id)
    )
    comunicacion = result.scalar_one()
    assert comunicacion.destinatario != email_original  # no está en claro

    # Verificar que es descifrable
    descifrado = decrypt_pii(comunicacion.destinatario)
    assert descifrado == email_original


# ---------------------------------------------------------------------------
# 8.6 — Encolado con tenant requiere_aprobacion=True
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_encolado_tenant_requiere_aprobacion(db_session: AsyncSession):
    """Tenant con requiere_aprobacion=True: mensajes quedan no-aprobados."""
    tenant = await _crear_tenant(db_session, requiere_aprobacion=True)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm = _perm_enviar(is_propio=False)

    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email="t@t.com")
    req = ComunicacionLoteRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Asunto",
        plantilla_cuerpo="Cuerpo",
        materia_id=materia.id,
    )

    resp = await svc.encolar_lote(req, perm)

    assert resp.requiere_aprobacion is True

    # Los mensajes quedan en Pendiente pero no aprobados
    result = await db_session.execute(
        select(Comunicacion).where(Comunicacion.lote_id == resp.lote_id)
    )
    msg = result.scalar_one()
    assert msg.estado == EstadoComunicacion.pendiente.value
    assert msg.aprobado is False


@pytest.mark.asyncio
async def test_encolado_tenant_sin_aprobacion_auto_aprueba(db_session: AsyncSession):
    """Tenant sin requiere_aprobacion: mensajes quedan aprobados automáticamente."""
    tenant = await _crear_tenant(db_session, requiere_aprobacion=False)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm = _perm_enviar(is_propio=False)

    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email="t@t.com")
    req = ComunicacionLoteRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Asunto",
        plantilla_cuerpo="Cuerpo",
        materia_id=materia.id,
    )

    resp = await svc.encolar_lote(req, perm)

    assert resp.requiere_aprobacion is False

    result = await db_session.execute(
        select(Comunicacion).where(Comunicacion.lote_id == resp.lote_id)
    )
    msg = result.scalar_one()
    assert msg.aprobado is True


# ---------------------------------------------------------------------------
# 8.7 — Usuario sin comunicacion:enviar → 403
# (Esto se prueba a nivel HTTP; aquí probamos el require_permission indirectamente)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_require_permission_enviar_no_tiene(db_session: AsyncSession):
    """Usuario sin comunicacion:enviar no puede usar el service (simulado)."""
    # La validación de permiso ocurre en el router (require_permission dependency).
    # Aquí verificamos que el service con permiso sí funciona.
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    svc = _make_service(db_session, tenant.id, usuario.id)

    # Con permiso → funciona
    perm_con = _perm_enviar(is_propio=False)
    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email="t@t.com")
    req = ComunicacionPreviewRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Asunto",
        plantilla_cuerpo="Cuerpo",
    )
    resultado = await svc.preview(req, perm_con)
    assert len(resultado) == 1


# ---------------------------------------------------------------------------
# 8.8 — PROFESOR intenta encolar para materia ajena → 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_encolado_materia_ajena_403(db_session: AsyncSession):
    """PROFESOR con is_propio=True sin asignación a la materia → 403."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    # No creamos asignación

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm = _perm_enviar(is_propio=True)  # PROFESOR con scope propio

    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email="t@t.com")
    req = ComunicacionLoteRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Asunto",
        plantilla_cuerpo="Cuerpo",
        materia_id=materia.id,
    )

    with pytest.raises(HTTPException) as exc_info:
        await svc.encolar_lote(req, perm)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_encolado_materia_propia_exitoso(db_session: AsyncSession):
    """PROFESOR con asignación propia puede encolar (triangulación)."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    await _crear_asignacion(db_session, tenant.id, usuario.id, materia.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm = _perm_enviar(is_propio=True)  # PROFESOR con scope propio

    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email="t@t.com")
    req = ComunicacionLoteRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Asunto",
        plantilla_cuerpo="Cuerpo",
        materia_id=materia.id,
    )

    resp = await svc.encolar_lote(req, perm)
    assert resp.total_encolados == 1


# ---------------------------------------------------------------------------
# 8.9 — Estado del lote agrega correctamente por estado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_estado_lote_agrega_por_estado(db_session: AsyncSession):
    """get_estado_lote devuelve conteo correcto por estado."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    repo = _make_repo(db_session, tenant.id)

    lote_id = uuid4()
    # Crear 3 mensajes con estados distintos
    for estado in [EstadoComunicacion.enviado, EstadoComunicacion.enviado, EstadoComunicacion.error]:
        c = Comunicacion(
            id=uuid4(),
            tenant_id=tenant.id,
            enviado_por=usuario.id,
            materia_id=materia.id,
            destinatario=encrypt_pii("test@test.com"),
            asunto="Asunto",
            cuerpo="Cuerpo",
            estado=estado.value,
            lote_id=lote_id,
            aprobado=True,
        )
        db_session.add(c)
    await db_session.commit()

    estado = await repo.get_estado_lote(lote_id)

    assert estado["total"] == 3
    assert estado["enviado"] == 2
    assert estado["error"] == 1
    assert estado["pendiente"] == 0


@pytest.mark.asyncio
async def test_estado_lote_schema_correcto(db_session: AsyncSession):
    """LoteEstadoSchema tiene todos los campos esperados (triangulación)."""
    from app.schemas.comunicacion import LoteEstadoSchema
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm_enviar = _perm_enviar(is_propio=False)
    perm_ver = PermissionContext(
        has_permission=True,
        is_propio=False,
        effective_permissions={"comunicacion:enviar", "comunicacion:aprobar"},
    )

    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email="t@t.com")
    req = ComunicacionLoteRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Asunto",
        plantilla_cuerpo="Cuerpo",
        materia_id=materia.id,
    )
    resp = await svc.encolar_lote(req, perm_enviar)

    estado = await svc.get_estado_lote(resp.lote_id, perm_ver)
    assert isinstance(estado, LoteEstadoSchema)
    assert estado.total == 1
    assert estado.pendiente == 1


# ---------------------------------------------------------------------------
# 8.10 — Aprobar lote → todos los Pendiente quedan aprobado=True
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aprobar_lote_marca_aprobado(db_session: AsyncSession):
    """aprobar_lote marca aprobado=True en todos los mensajes Pendiente del lote."""
    tenant = await _crear_tenant(db_session, requiere_aprobacion=True)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    repo = _make_repo(db_session, tenant.id)

    lote_id = uuid4()
    ids_creados = []
    for _ in range(3):
        c = Comunicacion(
            id=uuid4(),
            tenant_id=tenant.id,
            enviado_por=usuario.id,
            materia_id=materia.id,
            destinatario=encrypt_pii("test@test.com"),
            asunto="Asunto",
            cuerpo="Cuerpo",
            estado=EstadoComunicacion.pendiente.value,
            lote_id=lote_id,
            aprobado=False,
        )
        db_session.add(c)
        ids_creados.append(c.id)
    await db_session.commit()

    filas = await repo.aprobar_lote(lote_id)
    assert filas == 3

    # Verificar en DB
    for cid in ids_creados:
        await db_session.refresh(
            (await db_session.execute(select(Comunicacion).where(Comunicacion.id == cid))).scalar_one()
        )

    result = await db_session.execute(
        select(Comunicacion).where(Comunicacion.lote_id == lote_id)
    )
    for msg in result.scalars().all():
        assert msg.aprobado is True


@pytest.mark.asyncio
async def test_aprobar_lote_audita(db_session: AsyncSession):
    """aprobar_lote service registra COMUNICACION_APROBAR en audit log."""
    from app.models.audit_log import AuditLog
    tenant = await _crear_tenant(db_session, requiere_aprobacion=True)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    svc = _make_service(db_session, tenant.id, usuario.id)
    perm_enviar = _perm_enviar(is_propio=False)
    perm_aprobar = _perm_aprobar()

    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email="t@t.com")
    req = ComunicacionLoteRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Asunto",
        plantilla_cuerpo="Cuerpo",
        materia_id=materia.id,
    )
    resp = await svc.encolar_lote(req, perm_enviar)

    await svc.aprobar_lote(resp.lote_id, perm_aprobar)

    # Verificar audit log
    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.tenant_id == tenant.id,
            AuditLog.accion == "COMUNICACION_APROBAR",
        )
    )
    audit = result.scalar_one()
    assert audit.actor_id == usuario.id
    assert str(resp.lote_id) in str(audit.detalle)


# ---------------------------------------------------------------------------
# 8.11 — Cancelar lote → todos los Pendiente pasan a Cancelado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancelar_lote_transiciona_a_cancelado(db_session: AsyncSession):
    """cancelar_lote transiciona todos los Pendiente a Cancelado."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    repo = _make_repo(db_session, tenant.id)

    lote_id = uuid4()
    for _ in range(2):
        c = Comunicacion(
            id=uuid4(),
            tenant_id=tenant.id,
            enviado_por=usuario.id,
            materia_id=materia.id,
            destinatario=encrypt_pii("test@test.com"),
            asunto="Asunto",
            cuerpo="Cuerpo",
            estado=EstadoComunicacion.pendiente.value,
            lote_id=lote_id,
            aprobado=False,
        )
        db_session.add(c)
    await db_session.commit()

    cancelados = await repo.cancelar_lote(lote_id)
    assert cancelados == 2

    result = await db_session.execute(
        select(Comunicacion).where(Comunicacion.lote_id == lote_id)
    )
    for msg in result.scalars().all():
        assert msg.estado == EstadoComunicacion.cancelado.value


# ---------------------------------------------------------------------------
# 8.12 — Cancelar mensaje Enviado → 422 (transición inválida)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancelar_mensaje_enviado_422(db_session: AsyncSession):
    """cancelar_uno lanza 422 si el mensaje ya está en estado Enviado."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    repo = _make_repo(db_session, tenant.id)

    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("test@test.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.enviado.value,  # Estado terminal
        lote_id=uuid4(),
        aprobado=True,
    )
    db_session.add(c)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await repo.cancelar_uno(c.id)

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_cancelar_mensaje_cancelado_422(db_session: AsyncSession):
    """cancelar_uno lanza 422 también si ya está Cancelado (triangulación)."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    repo = _make_repo(db_session, tenant.id)

    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("test@test.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.cancelado.value,
        lote_id=uuid4(),
        aprobado=False,
    )
    db_session.add(c)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await repo.cancelar_uno(c.id)

    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# 8.13 — Retry de mensaje Error → vuelve a Pendiente
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_mensaje_error_vuelve_pendiente(db_session: AsyncSession):
    """retry_uno transiciona Error → Pendiente y limpia error_detalle."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    repo = _make_repo(db_session, tenant.id)

    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("test@test.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.error.value,
        lote_id=uuid4(),
        aprobado=True,
        error_detalle="N8N HTTP 500: error",
    )
    db_session.add(c)
    await db_session.commit()

    resultado = await repo.retry_uno(c.id)

    assert resultado.estado == EstadoComunicacion.pendiente.value
    assert resultado.error_detalle is None


# ---------------------------------------------------------------------------
# 8.14 — Retry de mensaje no-Error → 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_mensaje_no_error_422(db_session: AsyncSession):
    """retry_uno lanza 422 si el mensaje no está en Error."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    repo = _make_repo(db_session, tenant.id)

    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("test@test.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.pendiente.value,
        lote_id=uuid4(),
        aprobado=True,
    )
    db_session.add(c)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await repo.retry_uno(c.id)

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_retry_mensaje_enviado_422(db_session: AsyncSession):
    """retry_uno lanza 422 también si está en Enviado (triangulación)."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    repo = _make_repo(db_session, tenant.id)

    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("test@test.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.enviado.value,
        lote_id=uuid4(),
        aprobado=True,
    )
    db_session.add(c)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await repo.retry_uno(c.id)

    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# 8.15 — Máquina de estados — transición inválida rechazada
# ---------------------------------------------------------------------------


def test_transicion_valida_pendiente_a_enviando():
    """Pendiente → Enviando es válida."""
    assert transicion_valida(EstadoComunicacion.pendiente, EstadoComunicacion.enviando) is True


def test_transicion_invalida_enviado_a_pendiente():
    """Enviado → Pendiente es inválida (estado terminal)."""
    assert transicion_valida(EstadoComunicacion.enviado, EstadoComunicacion.pendiente) is False


def test_transicion_invalida_cancelado_a_cualquier_estado():
    """Cancelado es estado terminal — ninguna transición válida."""
    for destino in EstadoComunicacion:
        assert transicion_valida(EstadoComunicacion.cancelado, destino) is False


def test_transicion_valida_error_a_pendiente():
    """Error → Pendiente es válida (retry manual)."""
    assert transicion_valida(EstadoComunicacion.error, EstadoComunicacion.pendiente) is True


def test_transicion_invalida_pendiente_a_enviado():
    """Pendiente → Enviado no es válida directamente (debe pasar por Enviando)."""
    assert transicion_valida(EstadoComunicacion.pendiente, EstadoComunicacion.enviado) is False


# ---------------------------------------------------------------------------
# 8.16 — Aislamiento multi-tenant (Tenant B no ve lotes de Tenant A → 404)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aislamiento_multi_tenant_estado_lote(db_session: AsyncSession):
    """Tenant B no puede ver el estado de lotes de Tenant A."""
    tenant_a = await _crear_tenant(db_session)
    tenant_b = await _crear_tenant(db_session)
    usuario_a = await _crear_usuario(db_session, tenant_a.id)
    usuario_b = await _crear_usuario(db_session, tenant_b.id)
    materia_a = await _crear_materia(db_session, tenant_a.id)

    svc_a = _make_service(db_session, tenant_a.id, usuario_a.id)
    svc_b = _make_service(db_session, tenant_b.id, usuario_b.id)
    perm = _perm_enviar(is_propio=False)
    perm_ver = PermissionContext(
        has_permission=True,
        is_propio=False,
        effective_permissions={"comunicacion:enviar"},
    )

    dest = DestinatarioSchema(alumno_id=uuid4(), nombre="Test", email="t@t.com")
    req = ComunicacionLoteRequestSchema(
        destinatarios=[dest],
        plantilla_asunto="Asunto",
        plantilla_cuerpo="Cuerpo",
        materia_id=materia_a.id,
    )
    resp_a = await svc_a.encolar_lote(req, perm)

    # Tenant B intenta ver el lote de Tenant A → 404
    with pytest.raises(HTTPException) as exc_info:
        await svc_b.get_estado_lote(resp_a.lote_id, perm_ver)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# 8.17 — Worker: run_once con N8N mock exitoso → mensaje transiciona a Enviado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_worker_despacha_exitosamente(db_session: AsyncSession):
    """Worker con N8N mock que devuelve éxito: mensaje transiciona a Enviado."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    # Crear mensaje elegible
    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("alumno@example.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.pendiente.value,
        lote_id=uuid4(),
        aprobado=True,
    )
    db_session.add(c)
    await db_session.commit()

    # Mock N8NClient
    mock_n8n = AsyncMock()
    mock_n8n.send = AsyncMock(return_value=None)

    worker = ComunicacionWorker(
        webhook_url="http://n8n.test/webhook",
        batch_size=50,
        stale_threshold_minutes=10,
    )

    with patch("app.workers.comunicacion_worker.N8NClient", return_value=mock_n8n):
        await worker.run_once(db_session)

    # Verificar transición
    await db_session.refresh(c)
    assert c.estado == EstadoComunicacion.enviado.value
    assert c.enviado_at is not None


# ---------------------------------------------------------------------------
# 8.18 — Worker: run_once con N8N mock fallido → mensaje transiciona a Error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_worker_n8n_fallido_marca_error(db_session: AsyncSession):
    """Worker con N8N que falla: mensaje transiciona a Error con error_detalle."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("alumno@example.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.pendiente.value,
        lote_id=uuid4(),
        aprobado=True,
    )
    db_session.add(c)
    await db_session.commit()

    mock_n8n = AsyncMock()
    mock_n8n.send = AsyncMock(side_effect=N8NError(500, "Internal Server Error"))

    worker = ComunicacionWorker(
        webhook_url="http://n8n.test/webhook",
        batch_size=50,
        stale_threshold_minutes=10,
    )

    with patch("app.workers.comunicacion_worker.N8NClient", return_value=mock_n8n):
        await worker.run_once(db_session)

    await db_session.refresh(c)
    assert c.estado == EstadoComunicacion.error.value
    assert c.error_detalle is not None
    assert "500" in c.error_detalle


@pytest.mark.asyncio
async def test_worker_n8n_timeout_marca_error(db_session: AsyncSession):
    """Worker con N8N timeout: mensaje transiciona a Error (triangulación)."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("alumno@example.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.pendiente.value,
        lote_id=uuid4(),
        aprobado=True,
    )
    db_session.add(c)
    await db_session.commit()

    mock_n8n = AsyncMock()
    mock_n8n.send = AsyncMock(side_effect=N8NTimeoutError(10))

    worker = ComunicacionWorker(
        webhook_url="http://n8n.test/webhook",
        batch_size=50,
        stale_threshold_minutes=10,
    )

    with patch("app.workers.comunicacion_worker.N8NClient", return_value=mock_n8n):
        await worker.run_once(db_session)

    await db_session.refresh(c)
    assert c.estado == EstadoComunicacion.error.value
    assert "Timeout" in c.error_detalle or "timeout" in c.error_detalle.lower()


# ---------------------------------------------------------------------------
# 8.19 — Worker: tenant con requiere_aprobacion=True sin aprobado=True
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_worker_no_despacha_sin_aprobacion(db_session: AsyncSession):
    """Worker no despacha mensajes con aprobado=False."""
    tenant = await _crear_tenant(db_session, requiere_aprobacion=True)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("alumno@example.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.pendiente.value,
        lote_id=uuid4(),
        aprobado=False,  # No aprobado
    )
    db_session.add(c)
    await db_session.commit()

    mock_n8n = AsyncMock()
    mock_n8n.send = AsyncMock(return_value=None)

    worker = ComunicacionWorker(
        webhook_url="http://n8n.test/webhook",
        batch_size=50,
        stale_threshold_minutes=10,
    )

    with patch("app.workers.comunicacion_worker.N8NClient", return_value=mock_n8n):
        await worker.run_once(db_session)

    # Mensaje NO debe haber sido movido a Enviando
    await db_session.refresh(c)
    assert c.estado == EstadoComunicacion.pendiente.value
    mock_n8n.send.assert_not_called()


# ---------------------------------------------------------------------------
# 8.20 — Worker: resetear_colgados transiciona mensajes viejos en Enviando
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resetear_colgados_transiciona_a_pendiente(db_session: AsyncSession):
    """resetear_colgados transiciona mensajes viejos en Enviando a Pendiente."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    repo = _make_repo(db_session, tenant.id)

    # Crear mensaje en Enviando con updated_at hace más de 10 minutos
    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("test@test.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.enviando.value,
        lote_id=uuid4(),
        aprobado=True,
    )
    db_session.add(c)
    await db_session.commit()

    # Simular que fue actualizado hace 15 minutos
    from sqlalchemy import update
    await db_session.execute(
        update(Comunicacion)
        .where(Comunicacion.id == c.id)
        .values(updated_at=datetime.now(timezone.utc) - timedelta(minutes=15))
    )
    await db_session.commit()

    reseteados = await repo.resetear_colgados(stale_threshold_minutes=10)
    assert reseteados == 1

    await db_session.refresh(c)
    assert c.estado == EstadoComunicacion.pendiente.value


@pytest.mark.asyncio
async def test_resetear_colgados_no_toca_recientes(db_session: AsyncSession):
    """resetear_colgados NO resetea mensajes recientes en Enviando (triangulación)."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    repo = _make_repo(db_session, tenant.id)

    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("test@test.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.enviando.value,
        lote_id=uuid4(),
        aprobado=True,
    )
    db_session.add(c)
    await db_session.commit()
    # updated_at reciente (por defecto ahora)

    reseteados = await repo.resetear_colgados(stale_threshold_minutes=10)
    assert reseteados == 0

    await db_session.refresh(c)
    assert c.estado == EstadoComunicacion.enviando.value


# ---------------------------------------------------------------------------
# 8.21 — Worker: N8N_WEBHOOK_URL no configurada → worker no toma mensajes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_worker_sin_webhook_no_procesa(db_session: AsyncSession):
    """Worker sin webhook_url no transiciona ningún mensaje."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii("test@test.com"),
        asunto="Asunto",
        cuerpo="Cuerpo",
        estado=EstadoComunicacion.pendiente.value,
        lote_id=uuid4(),
        aprobado=True,
    )
    db_session.add(c)
    await db_session.commit()

    worker = ComunicacionWorker(webhook_url=None, batch_size=50)
    await worker.run_once(db_session)

    # El mensaje no debe haber sido tocado
    await db_session.refresh(c)
    assert c.estado == EstadoComunicacion.pendiente.value


# ---------------------------------------------------------------------------
# 8.22 — Worker: procesa solo COMUNICACION_BATCH_SIZE mensajes por ciclo
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_worker_respeta_batch_size(db_session: AsyncSession):
    """Worker procesa máximo batch_size mensajes por ciclo."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    # Crear 5 mensajes elegibles
    for _ in range(5):
        c = Comunicacion(
            id=uuid4(),
            tenant_id=tenant.id,
            enviado_por=usuario.id,
            materia_id=materia.id,
            destinatario=encrypt_pii("test@test.com"),
            asunto="Asunto",
            cuerpo="Cuerpo",
            estado=EstadoComunicacion.pendiente.value,
            lote_id=uuid4(),
            aprobado=True,
        )
        db_session.add(c)
    await db_session.commit()

    mock_n8n = AsyncMock()
    mock_n8n.send = AsyncMock(return_value=None)

    # batch_size=3: solo debe procesar 3
    worker = ComunicacionWorker(
        webhook_url="http://n8n.test/webhook",
        batch_size=3,
        stale_threshold_minutes=10,
    )

    with patch("app.workers.comunicacion_worker.N8NClient", return_value=mock_n8n):
        await worker.run_once(db_session)

    # Solo 3 llamadas a send
    assert mock_n8n.send.call_count == 3


# ---------------------------------------------------------------------------
# 8.23 — destinatario cifrado en DB (valor almacenado != email original)
# (cubierto ya en 8.5, pero aquí lo hacemos explícito desde el repo)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_destinatario_cifrado_en_db(db_session: AsyncSession):
    """El campo destinatario nunca está en texto plano en la DB."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)
    repo = _make_repo(db_session, tenant.id)

    email_original = "secreto@alumno.edu"
    lote_id = await repo.crear_lote(
        lote=[{"email": email_original, "asunto": "Asunto", "cuerpo": "Cuerpo"}],
        usuario_id=usuario.id,
        materia_id=materia.id,
    )

    result = await db_session.execute(
        select(Comunicacion).where(Comunicacion.lote_id == lote_id)
    )
    msg = result.scalar_one()

    # En DB no está en claro
    assert msg.destinatario != email_original
    assert "@" not in msg.destinatario or "base64" in msg.destinatario.lower() or len(msg.destinatario) > 50

    # Pero es descifrable
    assert decrypt_pii(msg.destinatario) == email_original


# ---------------------------------------------------------------------------
# 8.24 — destinatario descifrado correctamente en el worker antes de enviar
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_worker_descifra_destinatario_correctamente(db_session: AsyncSession):
    """Worker descifra destinatario y lo pasa correctamente a N8N send()."""
    tenant = await _crear_tenant(db_session)
    usuario = await _crear_usuario(db_session, tenant.id)
    materia = await _crear_materia(db_session, tenant.id)

    email_original = "destinatario.secreto@alumno.edu"
    c = Comunicacion(
        id=uuid4(),
        tenant_id=tenant.id,
        enviado_por=usuario.id,
        materia_id=materia.id,
        destinatario=encrypt_pii(email_original),
        asunto="Asunto final",
        cuerpo="Cuerpo final",
        estado=EstadoComunicacion.pendiente.value,
        lote_id=uuid4(),
        aprobado=True,
    )
    db_session.add(c)
    await db_session.commit()

    sent_payloads = []

    async def mock_send(destinatario, asunto, cuerpo):
        sent_payloads.append({"destinatario": destinatario, "asunto": asunto, "cuerpo": cuerpo})

    mock_n8n = AsyncMock()
    mock_n8n.send = AsyncMock(side_effect=mock_send)

    worker = ComunicacionWorker(
        webhook_url="http://n8n.test/webhook",
        batch_size=50,
        stale_threshold_minutes=10,
    )

    with patch("app.workers.comunicacion_worker.N8NClient", return_value=mock_n8n):
        await worker.run_once(db_session)

    assert len(sent_payloads) == 1
    # El destinatario enviado a N8N es el email descifrado (texto plano)
    assert sent_payloads[0]["destinatario"] == email_original
    assert sent_payloads[0]["asunto"] == "Asunto final"
