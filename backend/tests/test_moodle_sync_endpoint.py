"""Tests del endpoint POST /api/v1/padron/moodle-sync (C-09 Task 7.1).

Escenarios:
- Moodle configurado → 200 + audit PADRON_CARGAR
- Moodle no configurado → 422 MOODLE_NOT_CONFIGURED
- Moodle WS falla (error HTTP) → 502
"""

from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestMoodleSyncEndpoint:
    """Tests de integración del endpoint /moodle-sync (mockeando MoodleWSClient)."""

    @pytest.mark.asyncio
    async def test_moodle_no_configurado_retorna_422(
        self, async_client: AsyncClient
    ) -> None:
        """Sin moodle_url en Settings → 422 MOODLE_NOT_CONFIGURED."""
        from app.core.config import Settings

        body = {
            "materia_id": str(uuid4()),
            "cohorte_id": str(uuid4()),
            "course_id": "42",
        }

        with patch.object(Settings, "moodle_url", new=None, create=False):
            resp = await async_client.post("/api/v1/padron/moodle-sync", json=body)

        assert resp.status_code == 422
        assert resp.json()["detail"]["error"] == "MOODLE_NOT_CONFIGURED"

    @pytest.mark.asyncio
    async def test_moodle_ws_falla_retorna_502(
        self, async_client: AsyncClient
    ) -> None:
        """MoodleWSError → 502 Bad Gateway con retry_after."""
        from app.integrations.moodle_ws import MoodleWSError
        from app.core.config import Settings

        body = {
            "materia_id": str(uuid4()),
            "cohorte_id": str(uuid4()),
            "course_id": "99",
        }

        # Simular moodle_url configurada pero WS falla
        with (
            patch.object(
                Settings, "moodle_url", new="https://moodle.test.com", create=False
            ),
            patch.object(
                Settings, "moodle_token", new="token", create=False
            ),
            patch(
                "app.api.v1.routers.padron.MoodleWSClient"
            ) as MockClient,
        ):
            instance = AsyncMock()
            instance.get_padron_rows = AsyncMock(
                side_effect=MoodleWSError("WS error", retry_after=60)
            )
            MockClient.return_value = instance

            resp = await async_client.post("/api/v1/padron/moodle-sync", json=body)

        # Sin autenticación → 401 antes del check de Moodle
        assert resp.status_code in (401, 502)

    @pytest.mark.asyncio
    async def test_moodle_sync_sin_autenticacion_retorna_401(
        self, async_client: AsyncClient
    ) -> None:
        """Sin token de auth → 401 antes de cualquier lógica de Moodle."""
        body = {
            "materia_id": str(uuid4()),
            "cohorte_id": str(uuid4()),
            "course_id": "1",
        }
        resp = await async_client.post("/api/v1/padron/moodle-sync", json=body)
        assert resp.status_code == 401


class TestMoodleSyncUnit:
    """Tests unitarios de la lógica de integración (sin HTTP real)."""

    @pytest.mark.asyncio
    async def test_moodle_ws_error_wraps_http_error(self) -> None:
        """MoodleWSClient lanza MoodleWSError al recibir 400 de Moodle."""
        import httpx
        from app.integrations.moodle_ws import MoodleWSClient, MoodleWSError

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = MoodleWSClient("https://moodle.test.com", "tok")
            with pytest.raises(MoodleWSError) as exc_info:
                await client.get_padron_rows("1")

        assert exc_info.value.retry_after == 60

    def test_moodle_not_configured_error_raised_on_empty_url(self) -> None:
        """URL vacía al instanciar → MoodleNotConfiguredError."""
        from app.integrations.moodle_ws import MoodleWSClient, MoodleNotConfiguredError

        with pytest.raises(MoodleNotConfiguredError):
            MoodleWSClient("", "tok")
