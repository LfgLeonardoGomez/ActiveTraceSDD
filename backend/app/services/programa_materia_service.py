"""Service de programas y fechas académicas (C-17).

Orquesta repositories, valida reglas de negocio y aplica lógica de dominio.

Reglas duras:
- tenant_id y usuario_id SIEMPRE del JWT.
- Nunca lógica de negocio en Routers.
- Nunca acceso directo a DB desde este Service (siempre vía Repository).
"""

from datetime import datetime, timezone
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction, record_audit
from app.repositories.programa_materia_repository import (
    FechaAcademicaRepository,
    ProgramaMateriaRepository,
)
from app.schemas.programa_materia import (
    FechaAcademicaListResponseSchema,
    FechaAcademicaResponseSchema,
    LMSContentResponseSchema,
    ProgramaMateriaListResponseSchema,
    ProgramaMateriaResponseSchema,
)


class ProgramaMateriaService:
    """Service de programas de materia: CRUD + validación de unicidad."""

    def __init__(
        self,
        db_session: AsyncSession,
        tenant_id: UUID,
        usuario_id: UUID,
    ) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.usuario_id = usuario_id
        self._repo = ProgramaMateriaRepository(db_session, tenant_id)

    def _paginas(self, total: int, page_size: int) -> int:
        if page_size <= 0:
            return 0
        return ceil(total / page_size) if total > 0 else 0

    def _to_response_schema(self, programa) -> ProgramaMateriaResponseSchema:
        return ProgramaMateriaResponseSchema(
            id=programa.id,
            tenant_id=programa.tenant_id,
            materia_id=programa.materia_id,
            carrera_id=programa.carrera_id,
            cohorte_id=programa.cohorte_id,
            titulo=programa.titulo,
            referencia_archivo=programa.referencia_archivo,
            cargado_at=programa.cargado_at,
            created_at=programa.created_at,
            updated_at=programa.updated_at,
        )

    async def crear_programa(self, data: dict) -> ProgramaMateriaResponseSchema:
        """Crea un programa validando unicidad de combinación materia×carrera×cohorte."""
        count = await self._repo.count_by_combinacion(
            materia_id=data["materia_id"],
            carrera_id=data["carrera_id"],
            cohorte_id=data["cohorte_id"],
        )
        if count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un programa para esta combinación de materia, carrera y cohorte",
            )

        programa = await self._repo.create(data)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.PROGRAMA_CREAR,
            detalle={
                "programa_id": str(programa.id),
                "materia_id": str(programa.materia_id),
            },
        )
        return self._to_response_schema(programa)

    async def get_programa(self, programa_id: UUID) -> ProgramaMateriaResponseSchema:
        programa = await self._repo.get_by_id(programa_id)
        if programa is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Programa no encontrado",
            )
        return self._to_response_schema(programa)

    async def list_programas(
        self,
        materia_id: UUID,
        page: int,
        page_size: int,
    ) -> ProgramaMateriaListResponseSchema:
        items_raw, total = await self._repo.list_by_materia(
            materia_id=materia_id,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
        items = [self._to_response_schema(p) for p in items_raw]
        return ProgramaMateriaListResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )

    async def update_programa(
        self, programa_id: UUID, data: dict
    ) -> ProgramaMateriaResponseSchema:
        clean_data = {k: v for k, v in data.items() if v is not None}
        programa = await self._repo.update(programa_id, clean_data)
        if programa is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Programa no encontrado",
            )
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.PROGRAMA_ACTUALIZAR,
            detalle={"programa_id": str(programa.id)},
        )
        return self._to_response_schema(programa)

    async def delete_programa(self, programa_id: UUID) -> ProgramaMateriaResponseSchema:
        programa = await self._repo.get_by_id(programa_id)
        if programa is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Programa no encontrado",
            )
        await self._repo.soft_delete(programa_id)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.PROGRAMA_ELIMINAR,
            detalle={"programa_id": str(programa_id)},
        )
        return self._to_response_schema(programa)


class FechaAcademicaService:
    """Service de fechas académicas: CRUD + listado ordenado."""

    def __init__(
        self,
        db_session: AsyncSession,
        tenant_id: UUID,
        usuario_id: UUID,
    ) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.usuario_id = usuario_id
        self._repo = FechaAcademicaRepository(db_session, tenant_id)

    def _paginas(self, total: int, page_size: int) -> int:
        if page_size <= 0:
            return 0
        return ceil(total / page_size) if total > 0 else 0

    def _to_response_schema(self, fecha) -> FechaAcademicaResponseSchema:
        return FechaAcademicaResponseSchema(
            id=fecha.id,
            tenant_id=fecha.tenant_id,
            materia_id=fecha.materia_id,
            cohorte_id=fecha.cohorte_id,
            tipo=fecha.tipo,
            numero=fecha.numero,
            periodo=fecha.periodo,
            fecha=fecha.fecha,
            titulo=fecha.titulo,
            created_at=fecha.created_at,
            updated_at=fecha.updated_at,
        )

    async def crear_fecha(self, data: dict) -> FechaAcademicaResponseSchema:
        fecha = await self._repo.create(data)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.FECHA_CREAR,
            detalle={
                "fecha_id": str(fecha.id),
                "materia_id": str(fecha.materia_id),
                "tipo": fecha.tipo,
            },
        )
        return self._to_response_schema(fecha)

    async def get_fecha(self, fecha_id: UUID) -> FechaAcademicaResponseSchema:
        fecha = await self._repo.get_by_id(fecha_id)
        if fecha is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fecha académica no encontrada",
            )
        return self._to_response_schema(fecha)

    async def list_fechas(
        self,
        materia_id: UUID,
        page: int,
        page_size: int,
    ) -> FechaAcademicaListResponseSchema:
        items_raw, total = await self._repo.list_by_materia(
            materia_id=materia_id,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
        items = [self._to_response_schema(f) for f in items_raw]
        return FechaAcademicaListResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )

    async def list_fechas_por_cohorte(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        page: int,
        page_size: int,
    ) -> FechaAcademicaListResponseSchema:
        items_raw, total = await self._repo.list_by_materia_cohorte(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
        items = [self._to_response_schema(f) for f in items_raw]
        return FechaAcademicaListResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )

    async def update_fecha(
        self, fecha_id: UUID, data: dict
    ) -> FechaAcademicaResponseSchema:
        clean_data = {k: v for k, v in data.items() if v is not None}
        fecha = await self._repo.update(fecha_id, clean_data)
        if fecha is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fecha académica no encontrada",
            )
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.FECHA_ACTUALIZAR,
            detalle={"fecha_id": str(fecha.id)},
        )
        return self._to_response_schema(fecha)

    async def delete_fecha(self, fecha_id: UUID) -> FechaAcademicaResponseSchema:
        fecha = await self._repo.get_by_id(fecha_id)
        if fecha is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fecha académica no encontrada",
            )
        await self._repo.soft_delete(fecha_id)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.FECHA_ELIMINAR,
            detalle={"fecha_id": str(fecha_id)},
        )
        return self._to_response_schema(fecha)


class GeneracionLMSService:
    """Service para generar fragmento HTML de fechas académicas para el LMS."""

    def __init__(
        self,
        db_session: AsyncSession,
        tenant_id: UUID,
    ) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self._repo = FechaAcademicaRepository(db_session, tenant_id)

    async def generar_contenido_lms(
        self, materia_id: UUID, cohorte_id: UUID
    ) -> LMSContentResponseSchema:
        """Genera HTML con tabla de fechas académicas para el aula virtual."""
        fechas, _ = await self._repo.list_by_materia_cohorte(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            limit=100,
            offset=0,
        )

        if not fechas:
            return LMSContentResponseSchema(
                materia_id=materia_id,
                cohorte_id=cohorte_id,
                html="<p>No hay fechas académicas configuradas para esta materia y cohorte.</p>",
                cantidad_fechas=0,
            )

        rows = []
        for f in fechas:
            rows.append(
                f"<tr><td>{f.tipo}</td><td>{f.numero}</td><td>{f.fecha}</td><td>{f.titulo}</td></tr>"
            )

        html = (
            "<table border='1'><thead>"
            "<tr><th>Tipo</th><th>Número</th><th>Fecha</th><th>Título</th></tr>"
            "</thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )

        return LMSContentResponseSchema(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            html=html,
            cantidad_fechas=len(fechas),
        )
