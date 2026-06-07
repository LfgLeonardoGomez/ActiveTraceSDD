"""Router de health-check.

IMPLEMENTADO en C-01: GET /health reporta liveness + readiness de DB.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Endpoint de salud: reporta estado de la app y la base de datos."""
    try:
        await db.execute(text("SELECT 1"))
        database_status = "up"
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Health check DB failed: %s", exc, exc_info=True)
        database_status = "down"
    return {"status": "ok", "database": database_status}
