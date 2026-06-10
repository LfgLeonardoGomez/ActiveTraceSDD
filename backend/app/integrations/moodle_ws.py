"""Cliente Moodle Web Services (C-09).

Encapsula llamadas a core_enrol_get_enrolled_users y mapea la respuesta
a PadronImportRow para alimentar el pipeline de confirm_import.

Errores de red o HTTP >= 400 se convierten en MoodleWSError (nunca expone
el error crudo al caller — loggea en JSON estructurado).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.schemas.padron import PadronImportRow

logger = logging.getLogger(__name__)


class MoodleNotConfiguredError(Exception):
    """El tenant no tiene moodle_url configurada."""


class MoodleWSError(Exception):
    """Error al comunicarse con Moodle WS."""

    def __init__(self, message: str, retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class MoodleUser:
    id: int
    username: str
    firstname: str
    lastname: str
    email: str

    def to_padron_row(self) -> PadronImportRow:
        return PadronImportRow(
            nombre=self.firstname,
            apellidos=self.lastname,
            email=self.email,
        )


@dataclass
class SyncResult:
    course_id: str
    total: int
    errors: list[str]


class MoodleWSClient:
    """Cliente async para Moodle Web Services."""

    _WS_ENDPOINT = "/webservice/rest/server.php"
    _TIMEOUT = 30.0

    def __init__(self, moodle_url: str | None, token: str) -> None:
        if not moodle_url:
            raise MoodleNotConfiguredError("moodle_url is not configured for this tenant")
        self._base_url = moodle_url.rstrip("/")
        self._token = token

    async def get_enrolled_users(self, course_id: str) -> list[MoodleUser]:
        """Llama a core_enrol_get_enrolled_users y retorna lista de MoodleUser."""
        params = {
            "wstoken": self._token,
            "wsfunction": "core_enrol_get_enrolled_users",
            "moodlewsrestformat": "json",
            "courseid": course_id,
        }
        url = self._base_url + self._WS_ENDPOINT

        try:
            async with httpx.AsyncClient(timeout=self._TIMEOUT) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "moodle_ws_error",
                extra={
                    "event": "http_error",
                    "status_code": exc.response.status_code,
                    "course_id": course_id,
                },
            )
            raise MoodleWSError(
                f"Moodle WS returned HTTP {exc.response.status_code}",
                retry_after=60,
            ) from exc
        except httpx.TimeoutException as exc:
            logger.error(
                "moodle_ws_error",
                extra={"event": "timeout", "course_id": course_id},
            )
            raise MoodleWSError("Moodle WS request timed out", retry_after=60) from exc

        raw = response.json()
        try:
            users = [
                MoodleUser(
                    id=item["id"],
                    username=item["username"],
                    firstname=item["firstname"],
                    lastname=item["lastname"],
                    email=item["email"],
                )
                for item in raw
            ]
        except (KeyError, TypeError) as exc:
            logger.error(
                "moodle_ws_error",
                extra={"event": "schema_error", "course_id": course_id, "detail": str(exc)},
            )
            raise MoodleWSError("Moodle WS response schema is invalid") from exc

        return users

    async def get_padron_rows(self, course_id: str) -> list[PadronImportRow]:
        """Alias de alto nivel: usuarios matriculados → PadronImportRow."""
        users = await self.get_enrolled_users(course_id)
        return [u.to_padron_row() for u in users]
