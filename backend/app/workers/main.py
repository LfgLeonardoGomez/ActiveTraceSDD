"""Entrypoint del worker async.

Ejecuta tareas periódicas sin dependencia de APScheduler externo.
Tareas registradas:
- padron_sync: sync nocturna de padrón desde Moodle WS (cada 6 horas).
- comunicacion_dispatch: despacho de mensajes salientes vía N8N (cada 30 seg).
"""

import asyncio
import logging

from app.core.config import Settings
from app.core.logging import init_logging
from app.workers.comunicacion_worker import ComunicacionWorker
from app.workers.padron_sync_worker import PadronSyncWorker

logger = logging.getLogger(__name__)

_PADRON_SYNC_INTERVAL_SECONDS = 6 * 60 * 60  # 6 horas


async def _padron_sync_loop() -> None:
    """Loop periódico de sync de padrón. Obtiene configs desde la DB en cada ciclo."""
    worker = PadronSyncWorker()
    while True:
        try:
            # En producción, los tenants y configs se leerían desde la DB.
            # Aquí dejamos la infraestructura lista; la query se agrega cuando
            # C-06 exponga el modelo Tenant con moodle_url.
            await worker.run_once(tenants=[], sync_configs=[])
        except Exception:
            logger.exception("padron_sync_loop_unhandled_error")
        await asyncio.sleep(_PADRON_SYNC_INTERVAL_SECONDS)


async def _comunicacion_dispatch_loop() -> None:
    """Loop periódico de despacho de comunicaciones salientes vía N8N.

    Intervalo: COMUNICACION_DISPATCH_INTERVAL_SECONDS (default 30 seg).
    No procesa si N8N_WEBHOOK_URL no está configurada.
    """
    settings = Settings()
    worker = ComunicacionWorker(
        webhook_url=settings.n8n_webhook_url,
        batch_size=settings.comunicacion_batch_size,
        stale_threshold_minutes=settings.comunicacion_stale_threshold_minutes,
        n8n_timeout=settings.n8n_timeout_seconds,
    )
    interval = settings.comunicacion_dispatch_interval_seconds

    while True:
        try:
            from app.core.database import AsyncSessionLocal
            if AsyncSessionLocal is None:
                logger.warning("comunicacion_dispatch_loop_db_not_ready")
                await asyncio.sleep(interval)
                continue
            db_session = AsyncSessionLocal()
            try:
                await worker.run_once(db_session)
            finally:
                await db_session.close()
        except Exception:
            logger.exception("comunicacion_dispatch_loop_unhandled_error")
        await asyncio.sleep(interval)


async def main() -> None:
    """Arranca todos los loops de worker."""
    init_logging()
    logger.info("Worker started")
    await asyncio.gather(
        _padron_sync_loop(),
        _comunicacion_dispatch_loop(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped")
