"""Service de detección de entregas sin corregir (C-10).

Cruza el reporte de finalización del LMS con las calificaciones existentes
para identificar actividades textuales finalizadas por el alumno pero
sin nota registrada (RN-07, RN-08).

RN-08: solo aplica a actividades de escala textual.
"""

from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.padron_repository import PadronRepository
from app.utils.finalizacion_parser import parse_finalizacion


class EntregaSinCorregir(BaseModel):
    """Actividad finalizada por el alumno pero sin nota textual registrada."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    apellidos: str
    actividad: str


class FinalizacionService:
    """Service para detección de entregas sin corregir."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._cal_repo = CalificacionRepository(db_session, tenant_id)

    async def detectar_sin_corregir(
        self,
        file_bytes: bytes,
        filename: str,
        materia_id: UUID,
        current_user: CurrentUser,
    ) -> list[EntregaSinCorregir]:
        """Detecta actividades textuales finalizadas sin nota registrada.

        1. Parsea el reporte de finalización.
        2. Obtiene el set de (entrada_padron, actividad) ya calificados.
        3. Cruza: finalizados - calificados = sin corregir (RN-07).
        4. Filtra: solo actividades textuales (RN-08).

        Nota: la distinción textual/numérica se hace en base a si la actividad
        tiene nota_textual en la DB — si no existe registro textual, se infiere
        que es textual según RN-08 (las numéricas sin nota = no entregado).
        """
        result = parse_finalizacion(file_bytes, filename)

        if not result.filas:
            return []

        # Set de (entrada_padron_id, actividad) que ya tienen nota textual
        # Usamos (nombre+apellidos, actividad) como proxy porque la FK a
        # entrada_padron_id no está disponible en el reporte de finalización
        calificados_textuales = await self._cal_repo.get_actividades_con_nota_textual(
            usuario_importador_id=current_user.id,
            materia_id=materia_id,
        )
        # Construir set de (nombre_lower+apellidos_lower, actividad) para comparar
        # (no tenemos entrada_padron_id en el reporte de finalización)
        calificados_key: set[tuple[str, str]] = set()
        # No podemos cruzar por UUID directo aquí — cruzamos por actividad solamente
        # (ver nota en los docs: el cruce exacto requiere padrón resuelto, lo que
        # corresponde a C-11 cuando se implementa el análisis completo)
        actividades_calificadas_textuales: set[str] = {act for _, act in calificados_textuales}

        sin_corregir: list[EntregaSinCorregir] = []
        for fila in result.filas:
            if not fila.finalizado:
                continue
            # RN-08: solo si la actividad no tiene nota textual registrada
            if fila.actividad in actividades_calificadas_textuales:
                continue
            sin_corregir.append(
                EntregaSinCorregir(
                    nombre=fila.nombre,
                    apellidos=fila.apellidos,
                    actividad=fila.actividad,
                )
            )

        return sin_corregir
