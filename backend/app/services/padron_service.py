"""Service del padrón de alumnos (C-09).

Pipeline de importación en dos fases:
1. parse_file + generate_preview: parsea, valida, retorna resumen sin persistir.
2. confirm_import: persiste versión + entradas, activa versión, registra audit.

Resolución de usuario_id: al importar, se busca el email en la tabla de usuarios
del tenant. Si hay match → usuario_id resuelto; si no → None (válido).

El cifrado del email ocurre exclusivamente en PadronRepository.
"""

import csv
import io
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction, record_audit
from app.repositories.padron_repository import PadronRepository
from app.repositories.usuarios import UsuarioRepository
from app.schemas.padron import (
    PadronImportRow,
    PadronPreviewResponse,
    PadronRowError,
)

# Columnas obligatorias del archivo (case-insensitive después de normalizar)
_REQUIRED_COLUMNS = {"nombre", "apellidos", "email"}
_OPTIONAL_COLUMNS = {"comision", "regional"}
_ALL_KNOWN_COLUMNS = _REQUIRED_COLUMNS | _OPTIONAL_COLUMNS

# Primeras N filas que se incluyen en la muestra del preview
_PREVIEW_SAMPLE_SIZE = 5


def _normalize_header(h: str) -> str:
    """Normaliza un header: strip + lowercase."""
    return h.strip().lower()


class PadronService:
    """Service de gestión del padrón de alumnos.

    Métodos estáticos de parseo no requieren DB.
    Métodos de persistencia reciben la sesión en el constructor.
    """

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._padron_repo = PadronRepository(db_session, tenant_id)
        self._usuario_repo = UsuarioRepository(db_session, tenant_id)

    # ------------------------------------------------------------------
    # Fase 1: Parseo y Preview (sin DB)
    # ------------------------------------------------------------------

    @staticmethod
    def parse_file(
        content: bytes, filename: str
    ) -> tuple[list[PadronImportRow], list[PadronRowError]]:
        """Parsea un archivo xlsx o csv y retorna filas válidas + errores.

        Normaliza headers: case-insensitive, ignora espacios.
        Detecta columnas obligatorias faltantes → HTTPException 422.
        Filtra filas con email vacío → reporta en errores.

        Returns:
            (rows_validas, errores)
        """
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext == "xlsx":
            return PadronService._parse_xlsx(content)
        return PadronService._parse_csv(content)

    @staticmethod
    def _parse_csv(
        content: bytes,
    ) -> tuple[list[PadronImportRow], list[PadronRowError]]:
        text = content.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))

        raw_headers = reader.fieldnames or []
        normalized = {_normalize_header(h): h for h in raw_headers}

        missing = _REQUIRED_COLUMNS - set(normalized.keys())
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Columnas obligatorias faltantes: {', '.join(sorted(missing))}",
            )

        detected = [k for k in normalized if k in _ALL_KNOWN_COLUMNS]
        rows: list[PadronImportRow] = []
        errors: list[PadronRowError] = []

        for i, raw_row in enumerate(reader, start=2):
            row = {_normalize_header(k): (v or "").strip() for k, v in raw_row.items()}
            email = row.get("email", "")
            if not email:
                errors.append(PadronRowError(fila=i, mensaje="email vacío o faltante"))
                continue
            rows.append(
                PadronImportRow(
                    nombre=row.get("nombre", ""),
                    apellidos=row.get("apellidos", ""),
                    email=email,
                    comision=row.get("comision", ""),
                    regional=row.get("regional", ""),
                )
            )
        return rows, errors

    @staticmethod
    def _parse_xlsx(
        content: bytes,
    ) -> tuple[list[PadronImportRow], list[PadronRowError]]:
        try:
            import openpyxl
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="openpyxl es requerido para importar archivos .xlsx",
            )

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)

        raw_headers_row = next(rows_iter, None)
        if raw_headers_row is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Archivo vacío",
            )

        raw_headers = [str(h).strip() if h is not None else "" for h in raw_headers_row]
        normalized = {_normalize_header(h): idx for idx, h in enumerate(raw_headers)}

        missing = _REQUIRED_COLUMNS - set(normalized.keys())
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Columnas obligatorias faltantes: {', '.join(sorted(missing))}",
            )

        def _cell(row: tuple, col: str) -> str:
            idx = normalized.get(col)
            if idx is None:
                return ""
            val = row[idx] if idx < len(row) else None
            return str(val).strip() if val is not None else ""

        rows: list[PadronImportRow] = []
        errors: list[PadronRowError] = []

        for i, row_data in enumerate(rows_iter, start=2):
            email = _cell(row_data, "email")
            if not email:
                errors.append(PadronRowError(fila=i, mensaje="email vacío o faltante"))
                continue
            rows.append(
                PadronImportRow(
                    nombre=_cell(row_data, "nombre"),
                    apellidos=_cell(row_data, "apellidos"),
                    email=email,
                    comision=_cell(row_data, "comision"),
                    regional=_cell(row_data, "regional"),
                )
            )

        wb.close()
        return rows, errors

    @staticmethod
    def generate_preview(
        rows: list[PadronImportRow],
        errors: list[PadronRowError],
    ) -> PadronPreviewResponse:
        """Genera el response de preview a partir de filas ya parseadas.

        No persiste nada. Retorna conteos, columnas detectadas y muestra.
        """
        detected = ["nombre", "apellidos", "email"]
        if any(r.comision for r in rows):
            detected.append("comision")
        if any(r.regional for r in rows):
            detected.append("regional")

        return PadronPreviewResponse(
            filas_validas=len(rows),
            filas_con_error=len(errors),
            columnas_detectadas=detected,
            errores=errors,
            muestra=rows[:_PREVIEW_SAMPLE_SIZE],
        )

    # ------------------------------------------------------------------
    # Fase 2: Confirm Import (con DB)
    # ------------------------------------------------------------------

    async def confirm_import(
        self,
        *,
        rows: list[PadronImportRow],
        materia_id: UUID,
        cohorte_id: UUID,
        cargado_por_id: UUID | None = None,
        origen: str = "manual",
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> Any:
        """Persiste una nueva versión del padrón y la activa.

        1. Crea VersionPadron (activa=False).
        2. Resuelve usuario_id para cada fila buscando email en Usuarios.
        3. Persiste EntradaPadron con emails cifrados.
        4. Activa la nueva versión (desactiva la anterior).
        5. Registra AuditLog PADRON_CARGAR.

        Returns:
            VersionPadron activa con los datos persistidos.
        """
        # Crear versión en estado inactivo
        version = await self._padron_repo.crear_version(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=cargado_por_id,
            origen=origen,
        )

        # Resolver usuario_id para cada fila
        entradas: list[dict] = []
        for row in rows:
            usuario = await self._usuario_repo.get_by_email_hash(row.email)
            entradas.append(
                {
                    "nombre": row.nombre,
                    "apellidos": row.apellidos,
                    "email": row.email,
                    "comision": row.comision,
                    "regional": row.regional,
                    "usuario_id": usuario.id if usuario else None,
                }
            )

        # Persistir entradas en batch
        await self._padron_repo.bulk_crear_entradas(version.id, entradas)

        # Activar la nueva versión (desactiva la anterior)
        version = await self._padron_repo.activar_version(
            version.id, materia_id, cohorte_id
        )

        # Auditar — detalle NO contiene emails en claro
        # Si actor_id es None (worker/sistema) se omite el audit
        # ya que la FK actor_id requiere un usuario existente.
        if cargado_por_id is not None:
            await record_audit(
                self.db_session,
                actor_id=cargado_por_id,
                tenant_id=self.tenant_id,
                accion=AuditAction.PADRON_CARGAR,
                materia_id=materia_id,
                filas_afectadas=len(rows),
                detalle={
                    "version_id": str(version.id),
                    "cohorte_id": str(cohorte_id),
                    "origen": origen,
                },
                ip=ip,
                user_agent=user_agent,
            )

        return version

    # ------------------------------------------------------------------
    # Vaciar padrón (scope-isolated)
    # ------------------------------------------------------------------

    async def vaciar_padron(
        self,
        *,
        materia_id: UUID,
        cargado_por_id: UUID,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> int:
        """Vacía el padrón de una materia para el scope del actor (RN-04).

        Solo elimina versiones cargadas POR el usuario actor para esta materia.
        No afecta datos de otros docentes en la misma materia.

        Returns:
            Número de versiones eliminadas.
        """
        deleted = await self._padron_repo.soft_delete_all_versions(
            materia_id=materia_id,
            cargado_por=cargado_por_id,
        )

        await record_audit(
            self.db_session,
            actor_id=cargado_por_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.PADRON_VACIAR,
            materia_id=materia_id,
            filas_afectadas=deleted,
            detalle={"versiones_eliminadas": deleted},
            ip=ip,
            user_agent=user_agent,
        )

        return deleted
