"""Service de calificaciones (C-10).

Pipeline de importación:
1. preview_import: parsea el archivo, devuelve actividades detectadas sin persistir.
2. confirm_import: recibe archivo + selección, persiste calificaciones con aprobado
   calculado según umbral vigente del docente, registra audit CALIFICACIONES_IMPORTAR.
3. vaciar_materia: soft delete scope-isolated (RN-04).

Lógica de aprobado (D-01 del design):
- nota_numerica >= umbral_pct → aprobado (umbral en puntos, escala 0-100)
- nota_textual in valores_aprobatorios → aprobado
- sin nota → aprobado = False
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction, record_audit
from app.core.dependencies import CurrentUser
from app.repositories.asignaciones import AsignacionRepository
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.umbral_repository import UmbralRepository
from app.schemas.calificacion import (
    ActividadDetectada,
    ImportConfirmResponse,
    ImportPreviewResponse,
)
from app.utils.lms_parser import parse_calificaciones

_DEFAULT_UMBRAL_PCT = 60
_DEFAULT_VALORES_APROBATORIOS = ["Satisfactorio", "Supera lo esperado"]
_MAX_FILE_SIZE = 5 * 1024 * 1024


class CalificacionService:
    """Service de gestión de calificaciones.

    Requiere instanciación por request con sesión DB y tenant_id del JWT.
    """

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._cal_repo = CalificacionRepository(db_session, tenant_id)
        self._umbral_repo = UmbralRepository(db_session, tenant_id)
        self._asig_repo = AsignacionRepository(db_session, tenant_id)

    # ------------------------------------------------------------------
    # Fase 1: Preview (sin persistencia)
    # ------------------------------------------------------------------

    async def preview_import(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> ImportPreviewResponse:
        """Parsea el archivo y devuelve actividades detectadas sin persistir."""
        result = parse_calificaciones(file_bytes, filename)

        actividades_out = [
            ActividadDetectada(
                nombre=a.nombre,
                tipo=a.tipo,
                total_alumnos=len(result.filas),
                alumnos_con_valor=sum(
                    1 for f in result.filas if f.valores.get(a.nombre) is not None
                ),
            )
            for a in result.actividades
        ]

        return ImportPreviewResponse(
            actividades=actividades_out,
            total_alumnos=len(result.filas),
            advertencias=result.advertencias,
        )

    # ------------------------------------------------------------------
    # Fase 2: Confirm (persistencia + audit)
    # ------------------------------------------------------------------

    async def confirm_import(
        self,
        file_bytes: bytes,
        filename: str,
        materia_id: UUID,
        actividades_seleccionadas: list[str],
        current_user: CurrentUser,
        ip: str | None = None,
    ) -> ImportConfirmResponse:
        """Persiste calificaciones de las actividades seleccionadas.

        Calcula aprobado según umbral vigente del docente en la materia.
        Registra audit CALIFICACIONES_IMPORTAR.
        """
        result = parse_calificaciones(file_bytes, filename)

        actividades_set = set(actividades_seleccionadas)
        actividades_validas = {a.nombre: a for a in result.actividades if a.nombre in actividades_set}

        if not actividades_validas:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ninguna de las actividades seleccionadas fue detectada en el archivo.",
            )

        # Obtener umbral vigente del docente en esta materia
        asignaciones, _ = await self._asig_repo.list_paginated(
            usuario_id=current_user.id,
            materia_id=materia_id,
            incluir_vencidas=False,
            limit=1,
        )
        asignacion = asignaciones[0] if asignaciones else None

        umbral_pct = _DEFAULT_UMBRAL_PCT
        valores_aprobatorios_lower: set[str] = {v.lower() for v in _DEFAULT_VALORES_APROBATORIOS}

        if asignacion:
            umbral = await self._umbral_repo.get_by_asignacion(asignacion.id, materia_id)
            if umbral:
                umbral_pct = umbral.umbral_pct
                valores_aprobatorios_lower = {v.lower() for v in umbral.valores_aprobatorios}

        # Construir filas para bulk_upsert
        ahora = datetime.now(timezone.utc)
        filas: list[dict] = []
        alumnos_set: set[str] = set()

        for fila in result.filas:
            for nombre_act, act in actividades_validas.items():
                valor_raw = fila.valores.get(nombre_act)
                if valor_raw is None:
                    continue

                nota_numerica: float | None = None
                nota_textual: str | None = None
                aprobado = False

                if act.tipo == "numerica":
                    try:
                        nota_numerica = float(str(valor_raw).replace(",", "."))
                        aprobado = nota_numerica >= umbral_pct
                    except (ValueError, TypeError):
                        continue
                else:
                    nota_textual = str(valor_raw)
                    aprobado = nota_textual.strip().lower() in valores_aprobatorios_lower

                filas.append(
                    {
                        "id": uuid4(),
                        "tenant_id": self.tenant_id,
                        "entrada_padron_id": fila.entrada_padron_id,
                        "materia_id": materia_id,
                        "usuario_importador_id": current_user.id,
                        "actividad": nombre_act,
                        "nota_numerica": nota_numerica,
                        "nota_textual": nota_textual,
                        "aprobado": aprobado,
                        "origen": "Importado",
                        "importado_at": ahora,
                        "created_at": ahora,
                        "updated_at": ahora,
                    }
                )
                alumnos_set.add(str(fila.nombre) + str(fila.apellidos))

        if not filas:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se encontraron filas válidas para importar.",
            )

        filas_importadas = await self._cal_repo.bulk_upsert(filas)

        await record_audit(
            self.db_session,
            actor_id=current_user.id,
            tenant_id=self.tenant_id,
            accion=AuditAction.CALIFICACIONES_IMPORTAR,
            materia_id=materia_id,
            detalle={"actividades": list(actividades_set), "filas": filas_importadas},
            filas_afectadas=filas_importadas,
            ip=ip,
        )

        return ImportConfirmResponse(
            filas_importadas=filas_importadas,
            actividades_incluidas=len(actividades_validas),
            alumnos_actualizados=len(alumnos_set),
        )

    # ------------------------------------------------------------------
    # Vaciar scope-isolated (RN-04)
    # ------------------------------------------------------------------

    async def vaciar_materia(
        self,
        materia_id: UUID,
        current_user: CurrentUser,
        ip: str | None = None,
    ) -> int:
        """Soft delete de las calificaciones del docente en la materia (RN-04).

        Solo afecta los datos del usuario que ejecuta la operación.
        """
        filas = await self._cal_repo.soft_delete_scope(
            usuario_importador_id=current_user.id,
            materia_id=materia_id,
        )
        return filas
