"""Entrypoint del worker async.

Ejecuta tareas periódicas sin dependencia de APScheduler externo.
Tarea registrada:
- padron_sync: sync nocturna de padrón desde Moodle WS (cada 6 horas).
"""

import asyncio
import logging

from app.core.logging import init_logging
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


async def main() -> None:
    """Arranca todos los loops de worker."""
    init_logging()
    logger.info("Worker started")
    await asyncio.gather(
        _padron_sync_loop(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped")
