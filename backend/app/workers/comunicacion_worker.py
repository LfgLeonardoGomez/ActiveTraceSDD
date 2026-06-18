"""Worker de despacho de comunicaciones salientes (C-12).

Patrón: asyncio loop idéntico a padron_sync_worker.py.
- run_once(db_session): una pasada completa de despacho.
- Al arrancar resetea mensajes colgados en Enviando.
- NO procesa si N8N_WEBHOOK_URL no está configurada.
- Toma hasta COMUNICACION_BATCH_SIZE mensajes por ciclo.
- Descifra destinatario SOLO en memoria al enviar (nunca en logs).

Máquina de estados por ciclo:
    Pendiente (aprobado=True) → Enviando → Enviado   (éxito)
                                          → Error     (fallo N8N)
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.encryption import decrypt_pii
from app.integrations.n8n_client import N8NClient, N8NError, N8NTimeoutError
from app.repositories.comunicacion_repository import ComunicacionRepository

logger = logging.getLogger(__name__)

# Sentinela para indicar que el worker no tiene webhook configurado
_WEBHOOK_NOT_CONFIGURED = "N8N_WEBHOOK_URL_NOT_CONFIGURED"


class ComunicacionWorker:
    """Despacha comunicaciones pendientes vía N8N webhook.

    Args:
        webhook_url: URL del webhook de N8N. None → worker en modo no-op.
        batch_size: Cantidad máxima de mensajes por ciclo.
        stale_threshold_minutes: Minutos en Enviando antes de resetear.
        n8n_timeout: Timeout en segundos para cada llamada a N8N.
    """

    def __init__(
        self,
        webhook_url: str | None,
        batch_size: int = 50,
        stale_threshold_minutes: int = 10,
        n8n_timeout: int = 10,
    ) -> None:
        self.webhook_url = webhook_url
        self.batch_size = batch_size
        self.stale_threshold_minutes = stale_threshold_minutes
        self.n8n_timeout = n8n_timeout

    async def startup_run(self, db_session: Any) -> int:
        """Reset stuck Enviando messages once at worker startup.

        Must be called once before the dispatch loop starts. Subsequent calls
        to run_once do NOT perform this reset (startup-only lifecycle).

        Note: first run_once does not depend on a prior successful startup_run —
        the existing AsyncSessionLocal is None guard handles not-ready state.

        Args:
            db_session: Async SQLAlchemy session (short-lived, caller closes it).

        Returns:
            Number of messages reset to Pendiente (0 if webhook not configured).
        """
        if not self.webhook_url:
            return 0

        from uuid import UUID as _UUID
        _FAKE_TENANT = _UUID("00000000-0000-0000-0000-000000000001")
        repo_global = _GlobalComunicacionRepository(db_session, _FAKE_TENANT)

        reseteados = await repo_global.resetear_colgados(self.stale_threshold_minutes)
        if reseteados > 0:
            logger.info(
                "comunicacion_worker_reset_colgados",
                extra={"event": "reset_colgados", "count": reseteados},
            )
        return reseteados

    async def run_once(self, db_session: Any) -> None:
        """Ejecuta una pasada completa del worker de despacho.

        Args:
            db_session: Sesión async de SQLAlchemy (inyectada desde el loop).
        """
        # 7.4 — No procesar si N8N_WEBHOOK_URL no está configurada
        if not self.webhook_url:
            logger.warning(
                "comunicacion_worker_no_webhook",
                extra={
                    "event": "worker_skip_no_webhook",
                    "detail": "N8N_WEBHOOK_URL no configurada; no se procesan mensajes",
                },
            )
            return

        # Repository without tenant scope — worker processes all tenants.
        # Global operations (get_todos_pendientes_elegibles) do not filter by
        # tenant_id; a fake UUID is used only to satisfy BaseRepository validation.
        from uuid import UUID as _UUID
        _FAKE_TENANT = _UUID("00000000-0000-0000-0000-000000000001")
        repo_global = _GlobalComunicacionRepository(db_session, _FAKE_TENANT)

        # Tomar batch de mensajes elegibles
        mensajes = await repo_global.get_todos_pendientes_elegibles(self.batch_size)

        if not mensajes:
            logger.debug(
                "comunicacion_worker_no_pending",
                extra={"event": "no_pending_messages"},
            )
            return

        logger.info(
            "comunicacion_worker_dispatch_start",
            extra={"event": "dispatch_start", "count": len(mensajes)},
        )

        n8n = N8NClient(self.webhook_url, timeout=self.n8n_timeout)

        for msg in mensajes:
            await self._despachar_uno(repo_global, n8n, msg)

    async def _despachar_uno(
        self,
        repo: _GlobalComunicacionRepository,
        n8n: N8NClient,
        msg: Any,
    ) -> None:
        """Despacha un mensaje individual vía N8N.

        Transiciona: Pendiente → Enviando → Enviado | Error
        Descifra destinatario en memoria; NUNCA lo loguea.
        """
        comunicacion_id = msg.id

        # Pendiente → Enviando
        await repo.marcar_enviando(comunicacion_id)

        # Descifrar destinatario SOLO en memoria
        try:
            destinatario_plain = decrypt_pii(msg.destinatario)
        except Exception as exc:
            logger.error(
                "comunicacion_worker_decrypt_error",
                extra={
                    "event": "decrypt_error",
                    "comunicacion_id": str(comunicacion_id),
                    "detail": str(exc),
                },
            )
            await repo.marcar_error(comunicacion_id, f"Error al descifrar destinatario: {exc}")
            return

        # Intentar despacho vía N8N
        try:
            await n8n.send(
                destinatario=destinatario_plain,
                asunto=msg.asunto,
                cuerpo=msg.cuerpo,
            )
            await repo.marcar_enviado(comunicacion_id)
            logger.info(
                "comunicacion_worker_enviado",
                extra={
                    "event": "message_sent",
                    "comunicacion_id": str(comunicacion_id),
                    "lote_id": str(msg.lote_id),
                },
            )
        except N8NTimeoutError as exc:
            detalle = f"Timeout N8N: {exc.timeout_seconds}s"
            await repo.marcar_error(comunicacion_id, detalle)
            logger.error(
                "comunicacion_worker_timeout",
                extra={
                    "event": "n8n_timeout",
                    "comunicacion_id": str(comunicacion_id),
                    "lote_id": str(msg.lote_id),
                },
            )
        except N8NError as exc:
            detalle = f"N8N HTTP {exc.status_code}: {exc.detail}"
            await repo.marcar_error(comunicacion_id, detalle)
            logger.error(
                "comunicacion_worker_n8n_error",
                extra={
                    "event": "n8n_error",
                    "comunicacion_id": str(comunicacion_id),
                    "lote_id": str(msg.lote_id),
                    "status_code": exc.status_code,
                },
            )
        except Exception as exc:
            detalle = f"Error inesperado: {type(exc).__name__}: {exc}"
            await repo.marcar_error(comunicacion_id, detalle)
            logger.exception(
                "comunicacion_worker_unexpected_error",
                extra={
                    "event": "unexpected_error",
                    "comunicacion_id": str(comunicacion_id),
                },
            )


class _GlobalComunicacionRepository(ComunicacionRepository):
    """Repository extendido para el worker (sin filtro de tenant en ops globales).

    El BaseRepository requiere un tenant_id no-None, pero las operaciones
    globales del worker (resetear_colgados, get_todos_pendientes_elegibles)
    no filtran por tenant. Usamos un UUID ficticio para pasar la validación.
    """
    pass
