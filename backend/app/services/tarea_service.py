"""Service de tareas y comentarios (C-16).

Orquesta queries del repository, valida reglas de negocio
y aplica lógica de dominio: state machine, approval, delegation.

Reglas duras:
- tenant_id y usuario_id SIEMPRE del JWT (PermissionContext/CurrentUser).
- Nunca lógica de negocio en Routers.
- Nunca acceso directo a DB desde este Service (siempre vía Repository).
"""

from datetime import datetime, timezone
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction, record_audit
from app.models.tarea import EstadoTarea
from app.repositories.tarea_repository import ComentarioTareaRepository, TareaRepository
from app.schemas.tarea import (
    ComentarioListResponseSchema,
    ComentarioResponseSchema,
    EstadoTarea,
    TareaListResponseSchema,
    TareaResponseSchema,
)


class TareaService:
    """Service de tareas: state machine, delegation, approval, audit."""

    def __init__(
        self,
        db_session: AsyncSession,
        tenant_id: UUID,
        usuario_id: UUID,
    ) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.usuario_id = usuario_id
        self._repo = TareaRepository(db_session, tenant_id)
        self._repo_comentario = ComentarioTareaRepository(db_session, tenant_id)

    def _paginas(self, total: int, page_size: int) -> int:
        if page_size <= 0:
            return 0
        return ceil(total / page_size) if total > 0 else 0

    def _to_response_schema(self, tarea) -> TareaResponseSchema:
        return TareaResponseSchema(
            id=tarea.id,
            tenant_id=tarea.tenant_id,
            titulo=tarea.titulo,
            descripcion=tarea.descripcion,
            criterio_cierre=tarea.criterio_cierre,
            estado=EstadoTarea(tarea.estado),
            aprobada=tarea.aprobada,
            devuelta=tarea.devuelta,
            asignado_a=tarea.asignado_a,
            asignado_por=tarea.asignado_por,
            revisada_por=tarea.revisada_por,
            revisada_at=tarea.revisada_at,
            materia_id=tarea.materia_id,
            contexto_id=tarea.contexto_id,
            created_at=tarea.created_at,
            updated_at=tarea.updated_at,
        )

    def _to_comentario_response_schema(self, comentario) -> ComentarioResponseSchema:
        return ComentarioResponseSchema(
            id=comentario.id,
            tarea_id=comentario.tarea_id,
            autor_id=comentario.autor_id,
            contenido=comentario.contenido,
            created_at=comentario.created_at,
            updated_at=comentario.updated_at,
        )

    # ------------------------------------------------------------------
    # 5.1 State machine
    # ------------------------------------------------------------------

    def _validar_transicion(
        self, tarea, nuevo_estado: str, actor_id: UUID
    ) -> None:
        """Valida transición de estado según el state machine.

        Raises HTTPException(422) si la transición es inválida.
        Raises HTTPException(403) si el actor no tiene permiso.
        """
        origen = tarea.estado
        destino = nuevo_estado

        # Verificar permiso de actor
        es_asignado = tarea.asignado_a == actor_id
        es_asignador = tarea.asignado_por == actor_id
        if not es_asignado and not es_asignador:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés permiso para modificar esta tarea",
            )

        # Transiciones válidas
        validas = {
            (EstadoTarea.PENDIENTE, EstadoTarea.EN_PROGRESO): True,
            (EstadoTarea.EN_PROGRESO, EstadoTarea.RESUELTA): True,
            (EstadoTarea.EN_PROGRESO, EstadoTarea.CANCELADA): True,
            (EstadoTarea.RESUELTA, EstadoTarea.EN_PROGRESO): False,  # solo via devolver
            (EstadoTarea.RESUELTA, EstadoTarea.CANCELADA): True,
            (EstadoTarea.PENDIENTE, EstadoTarea.CANCELADA): True,
        }

        key = (origen, destino)
        if key not in validas:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Transición de estado inválida: {origen} → {destino}",
            )

        # Si es cancelada, assignee o assigner pueden hacerlo
        if destino == EstadoTarea.CANCELADA:
            return

        # Si es En progreso desde Pendiente, solo assignee
        if key == (EstadoTarea.PENDIENTE, EstadoTarea.EN_PROGRESO):
            if not es_asignado:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tenés permiso para modificar esta tarea",
                )
            return

        # Si es Resuelta desde En progreso, solo assignee
        if key == (EstadoTarea.EN_PROGRESO, EstadoTarea.RESUELTA):
            if not es_asignado:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tenés permiso para modificar esta tarea",
                )
            return

        # Cualquier otra válida (que no debería existir, pero por si acaso)
        if not validas[key]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Transición de estado inválida: {origen} → {destino}",
            )

    # ------------------------------------------------------------------
    # 5.2 CRUD
    # ------------------------------------------------------------------

    async def crear(self, data: dict) -> TareaResponseSchema:
        tarea = await self._repo.create(data)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.TAREA_CREAR,
            detalle={"tarea_id": str(tarea.id)},
        )
        return self._to_response_schema(tarea)

    async def get_tarea(self, tarea_id: UUID) -> TareaResponseSchema:
        tarea = await self._repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        return self._to_response_schema(tarea)

    async def list_admin(
        self,
        filtros: dict,
        page: int,
        page_size: int,
    ) -> TareaListResponseSchema:
        items_raw, total = await self._repo.list_por_tenant(
            page=page,
            page_size=page_size,
            estado=filtros.get("estado"),
            asignado_a=filtros.get("asignado_a"),
            materia_id=filtros.get("materia_id"),
            search=filtros.get("search"),
        )
        items = [self._to_response_schema(t) for t in items_raw]
        return TareaListResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )

    async def list_mis_tareas(
        self,
        page: int,
        page_size: int,
        estado: str | None = None,
    ) -> TareaListResponseSchema:
        items_raw, total = await self._repo.list_por_asignado(
            asignado_a=self.usuario_id,
            page=page,
            page_size=page_size,
            estado=estado,
        )
        items = [self._to_response_schema(t) for t in items_raw]
        return TareaListResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )

    async def update_tarea(self, tarea_id: UUID, data: dict) -> TareaResponseSchema:
        clean_data = {k: v for k, v in data.items() if v is not None}
        tarea = await self._repo.update(tarea_id, clean_data)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.TAREA_ACTUALIZAR,
            detalle={"tarea_id": str(tarea.id)},
        )
        return self._to_response_schema(tarea)

    async def delete_tarea(self, tarea_id: UUID) -> TareaResponseSchema:
        tarea = await self._repo.soft_delete(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.TAREA_ELIMINAR,
            detalle={"tarea_id": str(tarea.id)},
        )
        return self._to_response_schema(tarea)

    # ------------------------------------------------------------------
    # 5.1 State machine actions
    # ------------------------------------------------------------------

    async def cambiar_estado(
        self, tarea_id: UUID, nuevo_estado: str, actor_id: UUID
    ) -> TareaResponseSchema:
        tarea = await self._repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        self._validar_transicion(tarea, nuevo_estado, actor_id)
        tarea.estado = nuevo_estado
        tarea.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(tarea)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.TAREA_ESTADO_CAMBIAR,
            detalle={"tarea_id": str(tarea.id), "nuevo_estado": nuevo_estado},
        )
        return self._to_response_schema(tarea)

    async def aprobar(self, tarea_id: UUID) -> TareaResponseSchema:
        tarea = await self._repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        if tarea.estado != EstadoTarea.RESUELTA:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Solo se puede aprobar una tarea Resuelta",
            )
        if tarea.asignado_por != self.usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés permiso para modificar esta tarea",
            )
        tarea.aprobada = True
        tarea.revisada_por = self.usuario_id
        tarea.revisada_at = datetime.now(timezone.utc)
        tarea.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(tarea)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.TAREA_APROBAR,
            detalle={"tarea_id": str(tarea.id)},
        )
        return self._to_response_schema(tarea)

    async def devolver(self, tarea_id: UUID, observacion: str) -> TareaResponseSchema:
        tarea = await self._repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        if tarea.estado != EstadoTarea.RESUELTA:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Solo se puede devolver una tarea Resuelta",
            )
        if tarea.asignado_por != self.usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés permiso para modificar esta tarea",
            )
        tarea.devuelta = True
        tarea.estado = EstadoTarea.EN_PROGRESO
        tarea.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(tarea)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.TAREA_DEVOLVER,
            detalle={"tarea_id": str(tarea.id), "observacion": observacion},
        )
        return self._to_response_schema(tarea)

    async def delegar(self, tarea_id: UUID, nuevo_asignado_id: UUID) -> TareaResponseSchema:
        tarea = await self._repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        tarea.asignado_a = nuevo_asignado_id
        tarea.updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
        await self.db_session.refresh(tarea)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.TAREA_DELEGAR,
            detalle={"tarea_id": str(tarea.id), "nuevo_asignado_id": str(nuevo_asignado_id)},
        )
        return self._to_response_schema(tarea)

    # ------------------------------------------------------------------
    # 5.2 Comentarios
    # ------------------------------------------------------------------

    async def crear_comentario(self, tarea_id: UUID, data: dict) -> ComentarioResponseSchema:
        tarea = await self._repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        comentario = await self._repo_comentario.create({
            "tarea_id": tarea_id,
            "autor_id": self.usuario_id,
            "contenido": data["contenido"],
        })
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.TAREA_COMENTAR,
            detalle={"tarea_id": str(tarea_id), "comentario_id": str(comentario.id)},
        )
        return self._to_comentario_response_schema(comentario)

    async def list_comentarios(
        self, tarea_id: UUID, page: int, page_size: int
    ) -> ComentarioListResponseSchema:
        tarea = await self._repo.get_by_id(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada",
            )
        items_raw, total = await self._repo_comentario.list_por_tarea(
            tarea_id=tarea_id,
            page=page,
            page_size=page_size,
        )
        items = [self._to_comentario_response_schema(c) for c in items_raw]
        return ComentarioListResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )

    async def delete_comentario(self, comentario_id: UUID) -> ComentarioResponseSchema:
        comentario = await self._repo_comentario._get_by_id(comentario_id)
        if comentario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comentario no encontrado",
            )
        if comentario.autor_id != self.usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el autor puede eliminar este comentario",
            )
        comentario = await self._repo_comentario.soft_delete(comentario_id)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.TAREA_COMENTARIO_ELIMINAR,
            detalle={"comentario_id": str(comentario_id)},
        )
        return self._to_comentario_response_schema(comentario)
