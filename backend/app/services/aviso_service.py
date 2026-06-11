"""Service de avisos y acknowledgment (C-15).

Orquesta queries del repository, valida reglas de negocio
y aplica lógica de dominio: audience, vigencia, ack idempotencia.

Reglas duras:
- tenant_id y usuario_id SIEMPRE del JWT (PermissionContext/CurrentUser).
- Nunca lógica de negocio en Routers.
- Nunca acceso directo a DB desde este Service (siempre vía Repository).
"""

from datetime import datetime, timezone
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction, record_audit
from app.repositories.aviso_repository import AvisoRepository
from app.schemas.aviso import (
    AcknowledgmentResponseSchema,
    AlcanceAviso,
    AvisoListResponseSchema,
    AvisoParaUsuarioListSchema,
    AvisoParaUsuarioSchema,
    AvisoResponseSchema,
    SeveridadAviso,
)


class AvisoService:
    """Service de avisos: lógica de negocio de anuncios y acknowledgment."""

    def __init__(
        self,
        db_session: AsyncSession,
        tenant_id: UUID,
        usuario_id: UUID,
    ) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.usuario_id = usuario_id
        self._repo = AvisoRepository(db_session, tenant_id)

    def _paginas(self, total: int, page_size: int) -> int:
        if page_size <= 0:
            return 0
        return ceil(total / page_size) if total > 0 else 0

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # 4.1 CRUD avisos
    # ------------------------------------------------------------------

    async def crear_aviso(self, data: dict) -> AvisoResponseSchema:
        aviso = await self._repo.create(data)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.AVISO_CREAR,
            detalle={"aviso_id": str(aviso.id), "alcance": aviso.alcance},
        )
        return self._to_response_schema(aviso)

    async def get_aviso(self, aviso_id: UUID) -> AvisoResponseSchema:
        aviso = await self._repo.get_by_id(aviso_id)
        if aviso is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )
        return self._to_response_schema(aviso)

    async def list_avisos(
        self,
        page: int,
        page_size: int,
        alcance: str | None = None,
        activo: bool | None = None,
        severidad: str | None = None,
    ) -> AvisoListResponseSchema:
        items_raw, total = await self._repo.list_avisos(
            page=page,
            page_size=page_size,
            alcance=alcance,
            activo=activo,
            severidad=severidad,
        )
        items = [self._to_response_schema(aviso) for aviso in items_raw]
        return AvisoListResponseSchema(
            items=items,
            total=total,
            page=page,
            pages=self._paginas(total, page_size),
        )

    async def update_aviso(
        self, aviso_id: UUID, data: dict
    ) -> AvisoResponseSchema:
        # Eliminar None values — solo actualizar los campos enviados
        clean_data = {k: v for k, v in data.items() if v is not None}
        aviso = await self._repo.update(aviso_id, clean_data)
        if aviso is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.AVISO_ACTUALIZAR,
            detalle={"aviso_id": str(aviso.id)},
        )
        return self._to_response_schema(aviso)

    async def delete_aviso(self, aviso_id: UUID) -> AvisoResponseSchema:
        aviso = await self._repo.soft_delete(aviso_id)
        if aviso is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.AVISO_ELIMINAR,
            detalle={"aviso_id": str(aviso.id)},
        )
        return self._to_response_schema(aviso)

    # ------------------------------------------------------------------
    # 4.2 Listar mis avisos (RN-19, RN-20)
    # ------------------------------------------------------------------

    async def list_mis_avisos(
        self, page: int, page_size: int
    ) -> AvisoParaUsuarioListSchema:
        now = self._now()
        rows, total = await self._repo.list_para_usuario(
            usuario_id=self.usuario_id,
            now=now,
            page=page,
            page_size=page_size,
        )
        # Filtrar acknowledged (RN-19: no mostrar avisos ya confirmados)
        visible = [(aviso, ack) for aviso, ack in rows if not ack]
        items = [
            AvisoParaUsuarioSchema(
                id=aviso.id,
                tenant_id=aviso.tenant_id,
                alcance=AlcanceAviso(aviso.alcance),
                materia_id=aviso.materia_id,
                cohorte_id=aviso.cohorte_id,
                rol_destino=aviso.rol_destino,
                severidad=SeveridadAviso(aviso.severidad),
                titulo=aviso.titulo,
                cuerpo=aviso.cuerpo,
                inicio_en=aviso.inicio_en,
                fin_en=aviso.fin_en,
                orden=aviso.orden,
                activo=aviso.activo,
                requiere_ack=aviso.requiere_ack,
                created_at=aviso.created_at,
                updated_at=aviso.updated_at,
                acknowledged=ack,
            )
            for aviso, ack in visible
        ]
        return AvisoParaUsuarioListSchema(
            items=items,
            total=len(items),
            page=page,
            pages=self._paginas(len(items), page_size),
        )

    # ------------------------------------------------------------------
    # 4.3 Confirmar aviso (RN-19)
    # ------------------------------------------------------------------

    async def confirmar_aviso(
        self, aviso_id: UUID
    ) -> AcknowledgmentResponseSchema:
        now = self._now()
        aviso = await self._repo.get_by_id(aviso_id)
        if aviso is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )

        # Verificar vigencia (RN-18)
        if not aviso.activo or aviso.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )
        if aviso.inicio_en > now or aviso.fin_en < now:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aviso no encontrado",
            )

        # Verificar no ack previamente (409 si duplicado)
        existing = await self._repo.get_acknowledgment(aviso_id, self.usuario_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Aviso ya confirmado",
            )

        ack = await self._repo.acknowledge(aviso_id, self.usuario_id)
        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.AVISO_CONFIRMAR,
            detalle={"aviso_id": str(aviso_id)},
        )
        return AcknowledgmentResponseSchema(
            id=ack.id,
            aviso_id=ack.aviso_id,
            usuario_id=ack.usuario_id,
            confirmado_at=ack.confirmado_at,
            created_at=ack.created_at,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _to_response_schema(self, aviso) -> AvisoResponseSchema:
        return AvisoResponseSchema(
            id=aviso.id,
            tenant_id=aviso.tenant_id,
            alcance=AlcanceAviso(aviso.alcance),
            materia_id=aviso.materia_id,
            cohorte_id=aviso.cohorte_id,
            rol_destino=aviso.rol_destino,
            severidad=SeveridadAviso(aviso.severidad),
            titulo=aviso.titulo,
            cuerpo=aviso.cuerpo,
            inicio_en=aviso.inicio_en,
            fin_en=aviso.fin_en,
            orden=aviso.orden,
            activo=aviso.activo,
            requiere_ack=aviso.requiere_ack,
            created_at=aviso.created_at,
            updated_at=aviso.updated_at,
        )
