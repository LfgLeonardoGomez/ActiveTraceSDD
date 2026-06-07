import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import app


class TestAppStartup:
    """Tests de TDD para arranque de la app — C-01."""

    def test_app_is_fastapi_instance(self):
        """RED: la app FastAPI se instancia sin error."""
        assert isinstance(app, FastAPI)

    @pytest.mark.asyncio
    async def test_app_lifespan_starts(self):
        """GREEN: la app arranca (lifespan) sin error."""
        async with LifespanManager(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/health")
                assert response.status_code == 200
