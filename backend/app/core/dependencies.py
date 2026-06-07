"""Dependencies de FastAPI para inyección de dependencias.

Slots reservados:
- get_current_user → C-03 (auth)
- get_tenant → C-02 (multi-tenancy)
- require_permission → C-04 (RBAC)
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import database


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency que provee una sesión async por request.

    Garantiza cierre de la sesión al finalizar la request,
    incluso ante excepción (no fuga de conexiones al pool).
    """
    session = database.AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()
