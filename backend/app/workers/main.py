"""Entrypoint mínimo del worker.

Placeholder para el proceso de jobs en background.
La tecnología real de la cola se definirá en ADR-003.
"""

import asyncio
import logging

from app.core.logging import init_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Loop no-op del worker."""
    init_logging()
    logger.info("Worker placeholder started")
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped")
