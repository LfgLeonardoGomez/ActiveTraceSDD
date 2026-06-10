"""Servicio de gestión de asignaciones de roles en contexto académico (C-07).

Reglas de negocio:
- Los FKs referenciados (usuario_id, materia_id, carrera_id, cohorte_id, responsable_id)
  deben existir en el mismo tenant (404 si no).
- Un usuario puede tener múltiples asignaciones simultáneas con distintos roles.
- No existe restricción de unicidad de asignación por usuario/rol/contexto.
- Soft delete siempre (nunca borrado físico).
- estado_vigencia se calcula dinámicamente como @property en el modelo Asignacion.

No accede directamente a DB: delega todo al AsignacionRepository.
"""

from datetime import date
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.repositories.asignaciones import AsignacionRepository
from app.repositories.usuarios import UsuarioRepository


class AsignacionService:
    """Servicio de gestión de asignaciones del tenant."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._repo = AsignacionRepository(db_session, tenant_id)
        self._usuario_repo = UsuarioRepository(db_session, tenant_id)

    async def _verify_usuario_en_tenant(self, usuario_id: UUID) -> None:
        """Verifica que el usuario existe en el tenant.

        Raises:
            HTTPException 404: si no existe.
        """
        usuario = await self._usuario_repo.get_by_id(usuario_id)
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado en el tenant",
            )

    async def crear_asignacion(
        self,
        usuario_id: UUID,
        rol: str,
        desde: date,
        hasta: date | None = None,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        comisiones: list[str] | None = None,
        responsable_id: UUID | None = None,
    ) -> Asignacion:
        """Crea una asignación de rol en contexto académico.

        Verifica que el usuario_id y responsable_id (si se provee) existen
        en el tenant antes de crear.

        Returns:
            Asignación creada.

        Raises:
            HTTPException 404: si usuario_id o responsable_id no existen en el tenant.
        """
        await self._verify_usuario_en_tenant(usuario_id)

        if responsable_id is not None:
            await self._verify_usuario_en_tenant(responsable_id)

        return await self._repo.create(
            usuario_id=usuario_id,
            rol=rol,
            desde=desde,
            hasta=hasta,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            comisiones=comisiones or [],
            responsable_id=responsable_id,
        )

    async def listar_asignaciones(
        self,
        limit: int = 50,
        offset: int = 0,
        usuario_id: UUID | None = None,
        rol: str | None = None,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        incluir_vencidas: bool = True,
        incluir_eliminadas: bool = False,
    ) -> tuple[list[Asignacion], int]:
        """Lista asignaciones del tenant con filtros opcionales.

        Returns:
            Tuple (items, total).
        """
        return await self._repo.list_paginated(
            limit=limit,
            offset=offset,
            usuario_id=usuario_id,
            rol=rol,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            incluir_vencidas=incluir_vencidas,
            incluir_eliminadas=incluir_eliminadas,
        )

    async def obtener_asignacion(self, asignacion_id: UUID) -> Asignacion:
        """Obtiene una asignación por ID dentro del tenant.

        Returns:
            Asignación encontrada.

        Raises:
            HTTPException 404: si no existe en el tenant.
        """
        asig = await self._repo.get_by_id(asignacion_id)
        if asig is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación no encontrada",
            )
        return asig

    async def actualizar_asignacion(
        self, asignacion_id: UUID, data: dict[str, Any]
    ) -> Asignacion:
        """Actualiza campos de una asignación (parcial).

        Returns:
            Asignación actualizada.

        Raises:
            HTTPException 404: si no existe.
        """
        await self.obtener_asignacion(asignacion_id)

        updated = await self._repo.update(asignacion_id, data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación no encontrada",
            )
        return updated

    async def eliminar_asignacion(self, asignacion_id: UUID) -> bool:
        """Soft delete de asignación (setea deleted_at).

        Returns:
            True si fue encontrado y eliminado.

        Raises:
            HTTPException 404: si no existe.
        """
        result = await self._repo.soft_delete(asignacion_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación no encontrada",
            )
        return True
