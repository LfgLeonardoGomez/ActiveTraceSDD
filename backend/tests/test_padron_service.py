"""Tests TDD para PadronService (C-09).

Strict TDD: RED → GREEN → TRIANGULATE.
- 3.2: tests escritos ANTES de implementar el service (RED phase)
- 3.3-3.5: implementación del service pasa estos tests (GREEN phase)
- 3.6: triangulación con caso mixto (alumnos con y sin cuenta de usuario)

Tests usan DB real (sin mocks — regla dura).
"""

import io
import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_padron_repository import (
    _crear_materia,
    _crear_carrera,
    _crear_cohorte,
    _crear_usuario,
)


def _make_csv(rows: list[dict]) -> bytes:
    """Genera un CSV simple para tests."""
    lines = ["nombre,apellidos,email,comision,regional"]
    for r in rows:
        lines.append(
            f"{r.get('nombre','N')},{r.get('apellidos','A')},"
            f"{r.get('email','e@e.com')},"
            f"{r.get('comision','')},"
            f"{r.get('regional','')}"
        )
    return "\n".join(lines).encode("utf-8")


def _make_xlsx(rows: list[dict]) -> bytes:
    """Genera un XLSX mínimo para tests usando openpyxl."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["nombre", "apellidos", "email", "comision", "regional"])
    for r in rows:
        ws.append([
            r.get("nombre", "N"),
            r.get("apellidos", "A"),
            r.get("email", "e@e.com"),
            r.get("comision", ""),
            r.get("regional", ""),
        ])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Grupo 1: parse_file — RED (antes de implementar el service)
# ---------------------------------------------------------------------------


class TestParseCsv:
    """Task 3.2 RED: parseo de CSV."""

    def test_parse_csv_columnas_validas(self) -> None:
        """RED: parsear CSV con columnas válidas retorna filas correctas."""
        from app.services.padron_service import PadronService

        csv_content = _make_csv([
            {"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com",
             "comision": "A", "regional": "BA"},
            {"nombre": "Ana", "apellidos": "Lopez", "email": "ana@test.com",
             "comision": "B", "regional": ""},
        ])

        rows, errors = PadronService.parse_file(csv_content, "padron.csv")

        assert len(rows) == 2
        assert len(errors) == 0
        assert rows[0].nombre == "Juan"
        assert rows[0].email == "juan@test.com"
        assert rows[1].apellidos == "Lopez"

    def test_parse_csv_headers_case_insensitive(self) -> None:
        """RED: headers en mayúsculas y con espacios son normalizados."""
        from app.services.padron_service import PadronService

        content = "NOMBRE , APELLIDOS , EMAIL ,COMISION,REGIONAL\n".encode()
        content += "Maria,Gomez,maria@test.com,C,Rosario\n".encode()

        rows, errors = PadronService.parse_file(content, "padron.csv")

        assert len(rows) == 1
        assert rows[0].nombre == "Maria"
        assert rows[0].email == "maria@test.com"

    def test_parse_csv_columnas_faltantes_retorna_error(self) -> None:
        """RED: CSV sin columna 'email' lanza error de columnas faltantes."""
        from app.services.padron_service import PadronService
        from fastapi import HTTPException

        content = "nombre,apellidos\nJuan,Perez\n".encode()

        with pytest.raises(HTTPException) as exc_info:
            PadronService.parse_file(content, "padron.csv")

        assert exc_info.value.status_code == 422
        assert "email" in str(exc_info.value.detail).lower()

    def test_parse_csv_fila_email_vacio_reportada_como_error(self) -> None:
        """RED: fila con email vacío es excluida y reportada en errores."""
        from app.services.padron_service import PadronService

        content = _make_csv([
            {"nombre": "Valido", "apellidos": "OK", "email": "valido@test.com"},
            {"nombre": "SinEmail", "apellidos": "Error", "email": ""},
        ])

        rows, errors = PadronService.parse_file(content, "padron.csv")

        assert len(rows) == 1
        assert rows[0].nombre == "Valido"
        assert len(errors) == 1
        assert errors[0].fila == 2

    def test_parse_xlsx_columnas_validas(self) -> None:
        """RED: parsear XLSX con columnas válidas retorna filas correctas."""
        from app.services.padron_service import PadronService

        content = _make_xlsx([
            {"nombre": "Carlos", "apellidos": "Diaz", "email": "carlos@test.com",
             "comision": "A", "regional": "Cordoba"},
        ])

        rows, errors = PadronService.parse_file(content, "padron.xlsx")

        assert len(rows) == 1
        assert rows[0].nombre == "Carlos"
        assert rows[0].regional == "Cordoba"

    def test_parse_csv_columna_regional_ausente_usa_vacio(self) -> None:
        """RED: columna regional ausente → regional='' en todas las entradas."""
        from app.services.padron_service import PadronService

        content = "nombre,apellidos,email,comision\n".encode()
        content += "Pedro,Santos,pedro@test.com,A\n".encode()

        rows, errors = PadronService.parse_file(content, "padron.csv")

        assert len(rows) == 1
        assert rows[0].regional == ""


# ---------------------------------------------------------------------------
# Grupo 2: generate_preview — no persiste nada
# ---------------------------------------------------------------------------


class TestGeneratePreview:
    """Task 3.4 RED: preview no persiste."""

    def test_generate_preview_cuenta_filas(self) -> None:
        """RED: generate_preview retorna conteos correctos."""
        from app.services.padron_service import PadronService
        from app.schemas.padron import PadronImportRow, PadronRowError

        rows = [
            PadronImportRow(nombre="A", apellidos="B", email="a@t.com"),
            PadronImportRow(nombre="C", apellidos="D", email="c@t.com"),
        ]
        errors = [PadronRowError(fila=3, mensaje="email vacío")]

        preview = PadronService.generate_preview(rows, errors)

        assert preview.filas_validas == 2
        assert preview.filas_con_error == 1

    def test_generate_preview_muestra_columnas_detectadas(self) -> None:
        """RED: generate_preview incluye las columnas detectadas."""
        from app.services.padron_service import PadronService
        from app.schemas.padron import PadronImportRow

        rows = [PadronImportRow(nombre="X", apellidos="Y", email="x@t.com",
                                comision="A", regional="BA")]

        preview = PadronService.generate_preview(rows, [])

        assert "email" in preview.columnas_detectadas


# ---------------------------------------------------------------------------
# Grupo 3: confirm_import — persiste y cifra
# ---------------------------------------------------------------------------


class TestConfirmImport:
    """Task 3.5 RED: confirm_import persiste, cifra email, resuelve usuario_id."""

    @pytest.mark.asyncio
    async def test_confirm_import_crea_version_activa(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED: confirm_import crea versión activa y entradas."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.services.padron_service import PadronService
        from app.schemas.padron import PadronImportRow

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-SVC-01")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-SVC-01")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        usuario = await _crear_usuario(db_session, default_tenant.id, "svc-doc@test.com")

        rows = [
            PadronImportRow(nombre="Alu1", apellidos="T", email="alu1@test.com"),
            PadronImportRow(nombre="Alu2", apellidos="T", email="alu2@test.com"),
        ]

        svc = PadronService(db_session, default_tenant.id)
        version = await svc.confirm_import(
            rows=rows,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            cargado_por_id=usuario.id,
        )

        assert version.activa is True
        assert version.materia_id == materia.id

        from app.repositories.padron_repository import PadronRepository
        repo = PadronRepository(db_session, default_tenant.id)
        entradas = await repo.get_entradas_by_version(version.id)
        assert len(entradas) == 2
        emails = {e.email for e in entradas}
        assert "alu1@test.com" in emails

    @pytest.mark.asyncio
    async def test_confirm_import_segunda_version_desactiva_primera(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: segunda importación desactiva la primera versión."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.services.padron_service import PadronService
        from app.schemas.padron import PadronImportRow
        from sqlalchemy import text

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-SVC-02")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-SVC-02")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        usuario = await _crear_usuario(db_session, default_tenant.id, "svc-doc2@test.com")

        svc = PadronService(db_session, default_tenant.id)

        v1 = await svc.confirm_import(
            rows=[PadronImportRow(nombre="V1", apellidos="T", email="v1@t.com")],
            materia_id=materia.id, cohorte_id=cohorte.id, cargado_por_id=usuario.id,
        )
        v2 = await svc.confirm_import(
            rows=[PadronImportRow(nombre="V2", apellidos="T", email="v2@t.com")],
            materia_id=materia.id, cohorte_id=cohorte.id, cargado_por_id=usuario.id,
        )

        assert v2.activa is True

        raw = await db_session.execute(
            text("SELECT activa FROM versiones_padron WHERE id = :vid"),
            {"vid": str(v1.id)},
        )
        row = raw.fetchone()
        assert row[0] is False, "v1 debe estar inactiva tras la segunda importación"


# ---------------------------------------------------------------------------
# Task 3.6 — Triangulación: mezcla de alumnos con y sin cuenta de usuario
# ---------------------------------------------------------------------------


class TestConfirmImportResolucionUsuario:
    """Task 3.6 TRIANGULATE: resolución de usuario_id para alumnos con y sin cuenta."""

    @pytest.mark.asyncio
    async def test_confirm_import_resuelve_usuario_id(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE: alumno con email de usuario existente → usuario_id resuelto.
        Alumno sin cuenta → usuario_id = None."""
        from app.models.padron import VersionPadron, EntradaPadron  # noqa
        from app.services.padron_service import PadronService
        from app.schemas.padron import PadronImportRow

        materia = await _crear_materia(db_session, default_tenant.id, "MAT-SVC-03")
        carrera = await _crear_carrera(db_session, default_tenant.id, "CAR-SVC-03")
        cohorte = await _crear_cohorte(db_session, default_tenant.id, carrera.id)
        actor = await _crear_usuario(db_session, default_tenant.id, "actor@test.com")

        # Crear un usuario que ES alumno (tiene cuenta en el sistema)
        alumno_con_cuenta = await _crear_usuario(
            db_session, default_tenant.id, "alumno_con_cuenta@test.com"
        )

        rows = [
            # Este alumno tiene cuenta
            PadronImportRow(nombre="Con", apellidos="Cuenta",
                            email="alumno_con_cuenta@test.com"),
            # Este alumno NO tiene cuenta en el sistema
            PadronImportRow(nombre="Sin", apellidos="Cuenta",
                            email="sin_cuenta@inexistente.com"),
        ]

        svc = PadronService(db_session, default_tenant.id)
        version = await svc.confirm_import(
            rows=rows,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            cargado_por_id=actor.id,
        )

        from app.repositories.padron_repository import PadronRepository
        repo = PadronRepository(db_session, default_tenant.id)
        entradas = await repo.get_entradas_by_version(version.id)

        con_cuenta = next(e for e in entradas if e.email == "alumno_con_cuenta@test.com")
        sin_cuenta = next(e for e in entradas if e.email == "sin_cuenta@inexistente.com")

        assert con_cuenta.usuario_id == alumno_con_cuenta.id, \
            "El alumno con cuenta debe tener usuario_id resuelto"
        assert sin_cuenta.usuario_id is None, \
            "El alumno sin cuenta debe tener usuario_id = None"
