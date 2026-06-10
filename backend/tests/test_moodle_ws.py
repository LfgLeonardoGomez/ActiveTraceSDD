"""Tests del cliente Moodle WS (C-09 Task 6.2 — TDD RED).

Escenarios cubiertos:
- sync exitosa: lista de usuarios mapeada a PadronImportRow
- error HTTP (status >= 400) → MoodleWSError con retry_after=60
- schema de respuesta inválido → MoodleWSError
- timeout → MoodleWSError con retry_after=60
- tenant sin moodle_url → MoodleNotConfiguredError
"""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import httpx

from app.integrations.moodle_ws import (
    MoodleNotConfiguredError,
    MoodleWSClient,
    MoodleWSError,
    MoodleUser,
)
from app.schemas.padron import PadronImportRow


MOODLE_URL = "https://moodle.example.com"
MOODLE_TOKEN = "fake-token-123"
COURSE_ID = "42"


def _moodle_user_payload(email: str = "user@test.com") -> dict:
    return {
        "id": 1,
        "username": "user1",
        "firstname": "Laura",
        "lastname": "Perez",
        "email": email,
    }


class TestMoodleWSClientEnrolledUsers:
    """Tests de get_enrolled_users con respuesta HTTP mockeada."""

    @pytest.mark.asyncio
    async def test_sync_exitosa_retorna_lista_padron_rows(self) -> None:
        """Respuesta HTTP 200 con lista válida → lista de PadronImportRow."""
        payload = [_moodle_user_payload("laura@test.com")]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = payload
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = MoodleWSClient(MOODLE_URL, MOODLE_TOKEN)
            rows = await client.get_padron_rows(COURSE_ID)

        assert len(rows) == 1
        assert isinstance(rows[0], PadronImportRow)
        assert rows[0].nombre == "Laura"
        assert rows[0].apellidos == "Perez"
        assert rows[0].email == "laura@test.com"

    @pytest.mark.asyncio
    async def test_sync_multiples_usuarios_retorna_lista_completa(self) -> None:
        """Triangulación: 3 usuarios → 3 filas."""
        payload = [
            {"id": 1, "username": "u1", "firstname": "A", "lastname": "B", "email": "a@test.com"},
            {"id": 2, "username": "u2", "firstname": "C", "lastname": "D", "email": "c@test.com"},
            {"id": 3, "username": "u3", "firstname": "E", "lastname": "F", "email": "e@test.com"},
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = payload
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = MoodleWSClient(MOODLE_URL, MOODLE_TOKEN)
            rows = await client.get_padron_rows(COURSE_ID)

        assert len(rows) == 3
        emails = {r.email for r in rows}
        assert emails == {"a@test.com", "c@test.com", "e@test.com"}

    @pytest.mark.asyncio
    async def test_error_http_400_lanza_moodle_ws_error(self) -> None:
        """HTTP 400 → MoodleWSError con retry_after=60."""
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
            client = MoodleWSClient(MOODLE_URL, MOODLE_TOKEN)
            with pytest.raises(MoodleWSError) as exc:
                await client.get_padron_rows(COURSE_ID)

        assert exc.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_error_http_500_lanza_moodle_ws_error(self) -> None:
        """Triangulación: HTTP 500 → también MoodleWSError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = MoodleWSClient(MOODLE_URL, MOODLE_TOKEN)
            with pytest.raises(MoodleWSError) as exc:
                await client.get_padron_rows(COURSE_ID)

        assert exc.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_timeout_lanza_moodle_ws_error(self) -> None:
        """Timeout de red → MoodleWSError con retry_after=60."""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = MoodleWSClient(MOODLE_URL, MOODLE_TOKEN)
            with pytest.raises(MoodleWSError) as exc:
                await client.get_padron_rows(COURSE_ID)

        assert exc.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_respuesta_schema_invalido_lanza_moodle_ws_error(self) -> None:
        """JSON sin los campos esperados → MoodleWSError."""
        bad_payload = [{"wrong_field": "oops"}]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = bad_payload
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = MoodleWSClient(MOODLE_URL, MOODLE_TOKEN)
            with pytest.raises(MoodleWSError):
                await client.get_padron_rows(COURSE_ID)


class TestMoodleNotConfigured:
    """Tests de MoodleNotConfiguredError."""

    def test_instanciar_client_sin_url_lanza_not_configured(self) -> None:
        """URL vacía → MoodleNotConfiguredError al instanciar."""
        with pytest.raises(MoodleNotConfiguredError):
            MoodleWSClient("", MOODLE_TOKEN)

    def test_instanciar_client_url_none_lanza_not_configured(self) -> None:
        """URL None → MoodleNotConfiguredError al instanciar."""
        with pytest.raises(MoodleNotConfiguredError):
            MoodleWSClient(None, MOODLE_TOKEN)


class TestMoodleUserDataclass:
    """Tests del dataclass MoodleUser."""

    def test_from_dict_campos_completos(self) -> None:
        """Parseado desde dict de la API Moodle."""
        data = {
            "id": 5,
            "username": "juan",
            "firstname": "Juan",
            "lastname": "Gomez",
            "email": "juan@uni.edu",
        }
        user = MoodleUser(**data)
        assert user.id == 5
        assert user.email == "juan@uni.edu"
        assert user.firstname == "Juan"

    def test_to_padron_row_mapeo_correcto(self) -> None:
        """MoodleUser.to_padron_row() produce PadronImportRow con campos mapeados."""
        user = MoodleUser(id=1, username="x", firstname="Ana", lastname="Rios", email="ana@uni.edu")
        row = user.to_padron_row()
        assert isinstance(row, PadronImportRow)
        assert row.nombre == "Ana"
        assert row.apellidos == "Rios"
        assert row.email == "ana@uni.edu"
        assert row.comision == ""
        assert row.regional == ""
