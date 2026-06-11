"""Service de comunicaciones salientes (C-12).

Ciclo de vida:
    preview → encolar → aprobar → despachar (worker) → trackear

Reglas duras:
    - tenant_id y usuario_id SIEMPRE del PermissionContext/CurrentUser (JWT).
    - is_propio=True → solo asignaciones del docente (verificar titularidad).
    - is_propio=False → acceso global al tenant.
    - destinatario NUNCA expuesto en respuestas ni logs.
    - Nunca lógica de negocio en Routers.
    - Nunca acceso directo a DB en Services (siempre vía Repository).
"""

import string
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditAction, record_audit
from app.models.tenant import Tenant
from app.repositories.asignaciones import AsignacionRepository
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.schemas.comunicacion import (
    ComunicacionLoteRequestSchema,
    ComunicacionLoteResponseSchema,
    ComunicacionPreviewItemSchema,
    ComunicacionPreviewRequestSchema,
    LoteEstadoSchema,
)
from app.schemas.rbac_schema import PermissionContext

# Variables de plantilla disponibles para sustitución
_VARIABLES_DISPONIBLES = {"alumno.nombre", "alumno.email"}


class ComunicacionService:
    """Service de comunicaciones salientes del tenant."""

    def __init__(
        self,
        db_session: AsyncSession,
        tenant_id: UUID,
        usuario_id: UUID,
    ) -> None:
        self.db_session = db_session
        self.tenant_id = tenant_id
        self.usuario_id = usuario_id
        self._repo = ComunicacionRepository(db_session, tenant_id)
        self._asig_repo = AsignacionRepository(db_session, tenant_id)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    async def _get_tenant(self) -> Tenant:
        """Obtiene el tenant del contexto actual."""
        result = await self.db_session.execute(
            select(Tenant).where(Tenant.id == self.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant no encontrado",
            )
        return tenant

    async def _verificar_titularidad_materia(self, materia_id: UUID) -> None:
        """Verifica que el usuario tiene asignación a la materia.

        Lanza 403 si no tiene ninguna asignación activa a esa materia.
        """
        asignaciones = await self._asig_repo.list(materia_id=materia_id)
        propias = [a for a in asignaciones if a.usuario_id == self.usuario_id]
        if not propias:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes asignación a esta materia",
            )

    def _renderizar_plantilla(
        self,
        plantilla: str,
        nombre: str,
        email: str,
    ) -> str:
        """Renderiza una plantilla con variables de alumno.

        Usa string.Template de stdlib con sintaxis ${alumno.nombre}.
        Soporta {{variable}} (convertido internamente) para compatibilidad.

        Raises:
            HTTPException 422: si la plantilla tiene variables no disponibles.
        """
        # Normalizar {{variable}} → ${variable} para string.Template
        normalizada = plantilla.replace("{{", "${").replace("}}", "}")

        variables_contexto = {
            "alumno.nombre": nombre,
            "alumno.email": email,
        }

        try:
            tmpl = string.Template(normalizada)
            # safe_substitute deja variables faltantes sin error → usamos substitute
            # para detectar variables inválidas
            return tmpl.substitute(variables_contexto)
        except KeyError as exc:
            variable_invalida = str(exc).strip("'")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Variable de plantilla '{variable_invalida}' no disponible. "
                    f"Variables permitidas: {sorted(_VARIABLES_DISPONIBLES)}"
                ),
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Plantilla inválida: {exc}",
            ) from exc

    # ------------------------------------------------------------------
    # 5.2 — Preview
    # ------------------------------------------------------------------

    async def preview(
        self,
        request: ComunicacionPreviewRequestSchema,
        permission_ctx: PermissionContext,
    ) -> list[ComunicacionPreviewItemSchema]:
        """Renderiza la plantilla por alumno sin persistir nada.

        No registra AuditLog (operación de lectura sin efectos).
        """
        resultados = []
        for dest in request.destinatarios:
            asunto = self._renderizar_plantilla(
                request.plantilla_asunto,
                nombre=dest.nombre,
                email=dest.email,
            )
            cuerpo = self._renderizar_plantilla(
                request.plantilla_cuerpo,
                nombre=dest.nombre,
                email=dest.email,
            )
            resultados.append(
                ComunicacionPreviewItemSchema(
                    alumno_id=dest.alumno_id,
                    asunto_renderizado=asunto,
                    cuerpo_renderizado=cuerpo,
                )
            )
        return resultados

    # ------------------------------------------------------------------
    # 5.3 — Encolar lote
    # ------------------------------------------------------------------

    async def encolar_lote(
        self,
        request: ComunicacionLoteRequestSchema,
        permission_ctx: PermissionContext,
    ) -> ComunicacionLoteResponseSchema:
        """Encola un lote de mensajes en estado Pendiente.

        Si is_propio=True (PROFESOR), verifica titularidad de la materia.
        Si el tenant requiere aprobación, los mensajes quedan no-aprobados.
        Si no requiere aprobación, los mensajes se crean con aprobado=True.
        """
        if permission_ctx.is_propio:
            await self._verificar_titularidad_materia(request.materia_id)

        tenant = await self._get_tenant()
        requiere_aprobacion = tenant.requiere_aprobacion_comunicaciones

        # Renderizar cada mensaje
        items_lote = []
        for dest in request.destinatarios:
            asunto = self._renderizar_plantilla(
                request.plantilla_asunto,
                nombre=dest.nombre,
                email=dest.email,
            )
            cuerpo = self._renderizar_plantilla(
                request.plantilla_cuerpo,
                nombre=dest.nombre,
                email=dest.email,
            )
            items_lote.append({
                "email": dest.email,
                "asunto": asunto,
                "cuerpo": cuerpo,
            })

        lote_id = await self._repo.crear_lote(
            lote=items_lote,
            usuario_id=self.usuario_id,
            materia_id=request.materia_id,
        )

        # Si no requiere aprobación, aprobar automáticamente
        if not requiere_aprobacion:
            await self._repo.aprobar_lote(lote_id)

        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.COMUNICACION_ENVIAR,
            materia_id=request.materia_id,
            detalle={"lote_id": str(lote_id), "total": len(items_lote)},
            filas_afectadas=len(items_lote),
        )

        return ComunicacionLoteResponseSchema(
            lote_id=lote_id,
            total_encolados=len(items_lote),
            requiere_aprobacion=requiere_aprobacion,
        )

    # ------------------------------------------------------------------
    # 5.4 — Estado del lote
    # ------------------------------------------------------------------

    async def get_estado_lote(
        self,
        lote_id: UUID,
        permission_ctx: PermissionContext,
    ) -> LoteEstadoSchema:
        """Devuelve el estado agregado del lote.

        Si is_propio=True, verifica que el usuario es el creador del lote.
        Si is_propio=False (comunicacion:aprobar), acceso global al tenant.
        """
        if permission_ctx.is_propio:
            # Verificar que el usuario es el creador de al menos un mensaje del lote
            from sqlalchemy import select as sa_select
            from app.models.comunicacion import Comunicacion
            result = await self.db_session.execute(
                sa_select(Comunicacion).where(
                    Comunicacion.tenant_id == self.tenant_id,
                    Comunicacion.lote_id == lote_id,
                    Comunicacion.enviado_por == self.usuario_id,
                    Comunicacion.deleted_at.is_(None),
                ).limit(1)
            )
            if result.scalar_one_or_none() is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes acceso a este lote",
                )

        estado = await self._repo.get_estado_lote(lote_id)

        if estado["total"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lote no encontrado",
            )

        return LoteEstadoSchema(**estado)

    # ------------------------------------------------------------------
    # 5.5 — Aprobar lote
    # ------------------------------------------------------------------

    async def aprobar_lote(
        self,
        lote_id: UUID,
        permission_ctx: PermissionContext,
    ) -> int:
        """Aprueba todos los mensajes Pendiente del lote.

        Requiere comunicacion:aprobar (is_propio siempre False para este permiso).
        """
        # Verificar que el lote existe en el tenant
        estado = await self._repo.get_estado_lote(lote_id)
        if estado["total"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lote no encontrado",
            )

        filas = await self._repo.aprobar_lote(lote_id)

        await record_audit(
            session=self.db_session,
            actor_id=self.usuario_id,
            tenant_id=self.tenant_id,
            accion=AuditAction.COMUNICACION_APROBAR,
            detalle={"lote_id": str(lote_id), "filas_aprobadas": filas},
            filas_afectadas=filas,
        )
        return filas

    # ------------------------------------------------------------------
    # 5.6 — Cancelar lote
    # ------------------------------------------------------------------

    async def cancelar_lote(
        self,
        lote_id: UUID,
        permission_ctx: PermissionContext,
    ) -> int:
        """Cancela todos los mensajes Pendiente del lote.

        Requiere comunicacion:aprobar.
        """
        estado = await self._repo.get_estado_lote(lote_id)
        if estado["total"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lote no encontrado",
            )

        return await self._repo.cancelar_lote(lote_id)

    # ------------------------------------------------------------------
    # 5.7 — Cancelar uno
    # ------------------------------------------------------------------

    async def cancelar_uno(
        self,
        comunicacion_id: UUID,
        permission_ctx: PermissionContext,
    ) -> None:
        """Cancela un mensaje individual.

        Si is_propio=True, verifica que el usuario es el creador del mensaje.
        """
        if permission_ctx.is_propio:
            from app.models.comunicacion import Comunicacion as ComunicacionModel
            result = await self.db_session.execute(
                select(ComunicacionModel).where(
                    ComunicacionModel.tenant_id == self.tenant_id,
                    ComunicacionModel.id == comunicacion_id,
                    ComunicacionModel.deleted_at.is_(None),
                )
            )
            comunicacion = result.scalar_one_or_none()
            if comunicacion is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comunicación no encontrada",
                )
            if comunicacion.enviado_por != self.usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes acceso a esta comunicación",
                )

        await self._repo.cancelar_uno(comunicacion_id)

    # ------------------------------------------------------------------
    # 5.8 — Retry uno
    # ------------------------------------------------------------------

    async def retry_uno(
        self,
        comunicacion_id: UUID,
        permission_ctx: PermissionContext,
    ) -> None:
        """Vuelve a encolar un mensaje en estado Error.

        Si is_propio=True, verifica que el usuario es el creador.
        """
        if permission_ctx.is_propio:
            from app.models.comunicacion import Comunicacion as ComunicacionModel
            result = await self.db_session.execute(
                select(ComunicacionModel).where(
                    ComunicacionModel.tenant_id == self.tenant_id,
                    ComunicacionModel.id == comunicacion_id,
                    ComunicacionModel.deleted_at.is_(None),
                )
            )
            comunicacion = result.scalar_one_or_none()
            if comunicacion is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comunicación no encontrada",
                )
            if comunicacion.enviado_por != self.usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes acceso a esta comunicación",
                )

        await self._repo.retry_uno(comunicacion_id)
