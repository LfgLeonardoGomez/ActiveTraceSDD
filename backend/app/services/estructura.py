"""Servicios de dominio para estructura académica (C-06): Carrera, Cohorte, Materia.

Reglas de negocio:
- Unicidad enforced en Service (409 semántico) + DB partial unique index (safety net) [D-03]
- "Carrera inactiva no admite cohortes activas" enforced en CohorteService [D-04]
  → Verificado en: crear cohorte, desactivar carrera (con cohortes activas → 409),
    reactivar cohorte bajo carrera inactiva → 409

Clean Architecture: Routers → Services → Repositories → Models.
Nunca lógica de negocio en Routers; nunca acceso directo a DB desde Services.
"""

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estructura import Carrera, Cohorte, Materia
from app.repositories.estructura import (
    CarreraRepository,
    CohorteRepository,
    MateriaRepository,
)


class CarreraService:
    """Lógica de negocio para Carrera."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.repo = CarreraRepository(db_session, tenant_id)
        self._cohorte_repo = CohorteRepository(db_session, tenant_id)

    async def crear_carrera(self, codigo: str, nombre: str, estado: str = "Activa") -> Carrera:
        """Crea una carrera nueva.

        Raises:
            HTTPException 409 si el código ya existe en el tenant.
        """
        if await self.repo.exists_by_codigo(codigo):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El código '{codigo}' ya existe en este tenant.",
            )
        return await self.repo.create(codigo=codigo, nombre=nombre, estado=estado)

    async def listar_carreras(
        self,
        limit: int = 50,
        offset: int = 0,
        estado: str | None = None,
    ) -> tuple[list[Carrera], int]:
        """Lista carreras paginadas con filtro opcional por estado."""
        return await self.repo.list_paginated(limit=limit, offset=offset, estado=estado)

    async def obtener_carrera(self, carrera_id: UUID) -> Carrera:
        """Obtiene carrera por ID.

        Raises:
            HTTPException 404 si no existe en el tenant.
        """
        carrera = await self.repo.get_by_id(carrera_id)
        if carrera is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carrera no encontrada.",
            )
        return carrera

    async def actualizar_carrera(
        self,
        carrera_id: UUID,
        data: dict,
    ) -> Carrera:
        """Actualiza campos de una carrera.

        Si el campo 'estado' se actualiza a Inactiva, delega en desactivar_carrera.
        Si el campo 'codigo' cambia, verifica unicidad.

        Raises:
            HTTPException 404 si no existe.
            HTTPException 409 si el nuevo código ya está en uso.
            HTTPException 409 si se desactiva carrera con cohortes activas.
        """
        carrera = await self.obtener_carrera(carrera_id)

        nuevo_codigo = data.get("codigo")
        nuevo_estado = data.get("estado")

        # Verificar unicidad del nuevo código
        if nuevo_codigo is not None and nuevo_codigo != carrera.codigo:
            if await self.repo.exists_by_codigo(nuevo_codigo, exclude_id=carrera_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El código '{nuevo_codigo}' ya existe en este tenant.",
                )

        # Si se cambia a Inactiva, verificar que no tenga cohortes activas
        if nuevo_estado == "Inactiva" and carrera.estado == "Activa":
            activas = await self._cohorte_repo.count_activas_por_carrera(carrera_id)
            if activas > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"La carrera tiene {activas} cohorte(s) activa(s). "
                           "Desactivá las cohortes antes de desactivar la carrera.",
                )

        actualizada = await self.repo.update(carrera_id, data)
        if actualizada is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carrera no encontrada.",
            )
        return actualizada

    async def desactivar_carrera(self, carrera_id: UUID) -> Carrera:
        """Cambia el estado de la carrera a Inactiva.

        Raises:
            HTTPException 409 si tiene cohortes activas.
            HTTPException 404 si no existe.
        """
        return await self.actualizar_carrera(carrera_id, {"estado": "Inactiva"})

    async def eliminar_carrera(self, carrera_id: UUID) -> bool:
        """Soft delete de carrera.

        Raises:
            HTTPException 404 si no existe.
        """
        await self.obtener_carrera(carrera_id)
        return await self.repo.soft_delete(carrera_id)


class CohorteService:
    """Lógica de negocio para Cohorte."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.repo = CohorteRepository(db_session, tenant_id)
        self._carrera_repo = CarreraRepository(db_session, tenant_id)

    async def _get_carrera_activa(self, carrera_id: UUID) -> Carrera:
        """Obtiene la carrera y valida que esté activa.

        Raises:
            HTTPException 404 si la carrera no existe.
            HTTPException 409 si la carrera está inactiva.
        """
        carrera = await self._carrera_repo.get_by_id(carrera_id)
        if carrera is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carrera no encontrada.",
            )
        if carrera.estado != "Activa":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La carrera está inactiva. No se pueden agregar o activar cohortes.",
            )
        return carrera

    async def crear_cohorte(
        self,
        carrera_id: UUID,
        nombre: str,
        anio: int,
        vig_desde: date,
        vig_hasta: date | None = None,
        estado: str = "Activa",
    ) -> Cohorte:
        """Crea una cohorte bajo una carrera activa.

        Raises:
            HTTPException 404 si la carrera no existe.
            HTTPException 409 si la carrera está inactiva.
            HTTPException 409 si ya existe una cohorte con el mismo nombre en la carrera.
        """
        await self._get_carrera_activa(carrera_id)

        if await self.repo.exists_by_nombre_en_carrera(carrera_id, nombre):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una cohorte '{nombre}' en esta carrera.",
            )

        return await self.repo.create(
            carrera_id=carrera_id,
            nombre=nombre,
            anio=anio,
            vig_desde=vig_desde,
            vig_hasta=vig_hasta,
            estado=estado,
        )

    async def listar_cohortes(
        self,
        limit: int = 50,
        offset: int = 0,
        estado: str | None = None,
        carrera_id: UUID | None = None,
    ) -> tuple[list[Cohorte], int]:
        """Lista cohortes paginadas con filtros opcionales."""
        return await self.repo.list_paginated(
            limit=limit, offset=offset, estado=estado, carrera_id=carrera_id
        )

    async def obtener_cohorte(self, cohorte_id: UUID) -> Cohorte:
        """Obtiene cohorte por ID.

        Raises:
            HTTPException 404 si no existe en el tenant.
        """
        cohorte = await self.repo.get_by_id(cohorte_id)
        if cohorte is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cohorte no encontrada.",
            )
        return cohorte

    async def actualizar_cohorte(self, cohorte_id: UUID, data: dict) -> Cohorte:
        """Actualiza campos de una cohorte.

        Si el estado cambia a Activa, valida que la carrera esté activa.

        Raises:
            HTTPException 404 si no existe.
            HTTPException 409 si se reactiva con carrera inactiva.
        """
        cohorte = await self.obtener_cohorte(cohorte_id)

        nuevo_estado = data.get("estado")
        if nuevo_estado == "Activa" and cohorte.estado != "Activa":
            await self._get_carrera_activa(cohorte.carrera_id)

        actualizada = await self.repo.update(cohorte_id, data)
        if actualizada is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cohorte no encontrada.",
            )
        return actualizada

    async def cambiar_estado_cohorte(self, cohorte_id: UUID, nuevo_estado: str) -> Cohorte:
        """Cambia el estado de una cohorte.

        Si se activa, verifica que la carrera esté activa.

        Raises:
            HTTPException 404 si no existe.
            HTTPException 409 si la carrera está inactiva (al reactivar).
        """
        return await self.actualizar_cohorte(cohorte_id, {"estado": nuevo_estado})

    async def eliminar_cohorte(self, cohorte_id: UUID) -> bool:
        """Soft delete de cohorte.

        Raises:
            HTTPException 404 si no existe.
        """
        await self.obtener_cohorte(cohorte_id)
        return await self.repo.soft_delete(cohorte_id)


class MateriaService:
    """Lógica de negocio para Materia."""

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        self.repo = MateriaRepository(db_session, tenant_id)

    async def crear_materia(
        self, codigo: str, nombre: str, estado: str = "Activa"
    ) -> Materia:
        """Crea una materia nueva.

        Raises:
            HTTPException 409 si el código ya existe en el tenant.
        """
        if await self.repo.exists_by_codigo(codigo):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El código '{codigo}' ya existe en este tenant.",
            )
        return await self.repo.create(codigo=codigo, nombre=nombre, estado=estado)

    async def listar_materias(
        self,
        limit: int = 50,
        offset: int = 0,
        estado: str | None = None,
    ) -> tuple[list[Materia], int]:
        """Lista materias paginadas con filtro opcional por estado."""
        return await self.repo.list_paginated(limit=limit, offset=offset, estado=estado)

    async def obtener_materia(self, materia_id: UUID) -> Materia:
        """Obtiene materia por ID.

        Raises:
            HTTPException 404 si no existe en el tenant.
        """
        materia = await self.repo.get_by_id(materia_id)
        if materia is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Materia no encontrada.",
            )
        return materia

    async def actualizar_materia(self, materia_id: UUID, data: dict) -> Materia:
        """Actualiza campos de una materia.

        Si el código cambia, verifica unicidad.

        Raises:
            HTTPException 404 si no existe.
            HTTPException 409 si el nuevo código ya está en uso en el tenant.
        """
        materia = await self.obtener_materia(materia_id)

        nuevo_codigo = data.get("codigo")
        if nuevo_codigo is not None and nuevo_codigo != materia.codigo:
            if await self.repo.exists_by_codigo(nuevo_codigo, exclude_id=materia_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El código '{nuevo_codigo}' ya existe en este tenant.",
                )

        actualizada = await self.repo.update(materia_id, data)
        if actualizada is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Materia no encontrada.",
            )
        return actualizada

    async def cambiar_estado_materia(self, materia_id: UUID, nuevo_estado: str) -> Materia:
        """Cambia el estado de una materia."""
        return await self.actualizar_materia(materia_id, {"estado": nuevo_estado})

    async def eliminar_materia(self, materia_id: UUID) -> bool:
        """Soft delete de materia.

        Raises:
            HTTPException 404 si no existe.
        """
        await self.obtener_materia(materia_id)
        return await self.repo.soft_delete(materia_id)
