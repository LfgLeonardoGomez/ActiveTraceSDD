import pytest
from sqlalchemy import text
from unittest.mock import AsyncMock, patch

from app.core.dependencies import get_db


class TestDatabaseConnection:
    """Tests de TDD para conexión a base de datos — C-01."""

    @pytest.mark.asyncio
    async def test_session_executes_select_one(self, db_session):
        """RED: una sesión async ejecuta SELECT 1 y obtiene resultado."""
        result = await db_session.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1

    @pytest.mark.asyncio
    async def test_get_db_closes_on_exception(self):
        """TRIANGULATE: la sesión se cierra ante excepción dentro del scope de get_db."""
        with patch("app.core.dependencies.AsyncSessionLocal") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value = mock_session
            gen = get_db()
            session = await anext(gen)
            try:
                await gen.athrow(RuntimeError, "forced error")
            except RuntimeError:
                pass
            mock_session.close.assert_awaited_once()
