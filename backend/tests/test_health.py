import pytest


class TestHealthCheck:
    """Tests de TDD para health-check — C-01."""

    @pytest.mark.asyncio
    async def test_health_returns_ok_and_database_up(self, async_client):
        """RED: GET /health responde 200 con JSON que incluye status y database: up."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "up"

    @pytest.mark.asyncio
    async def test_health_returns_database_down_when_db_unreachable(self, async_client, monkeypatch):
        """TRIANGULATE: el endpoint reporta database: down cuando la DB no responde."""
        from unittest.mock import AsyncMock
        from app.core import dependencies

        async def mock_get_db():
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("DB down")
            yield mock_session

        monkeypatch.setattr(dependencies, "get_db", mock_get_db)
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "down"
