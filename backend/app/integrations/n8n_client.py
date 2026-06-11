"""Cliente HTTP para N8N webhook de despacho de emails.

N8NClient encapsula el POST al webhook de N8N. Es inyectable (webhook_url
como parámetro de constructor) para facilitar mocking en tests.

Errores:
    N8NTimeoutError: el webhook no respondió en el tiempo configurado.
    N8NError: el webhook devolvió un error HTTP (4xx/5xx).
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class N8NError(Exception):
    """Error HTTP del webhook de N8N (4xx/5xx)."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"N8N webhook error {status_code}: {detail}")


class N8NTimeoutError(Exception):
    """Timeout al llamar al webhook de N8N."""

    def __init__(self, timeout_seconds: int) -> None:
        self.timeout_seconds = timeout_seconds
        super().__init__(f"N8N webhook timeout after {timeout_seconds}s")


class N8NClient:
    """Cliente HTTP async para el webhook de N8N.

    Args:
        webhook_url: URL completa del webhook de N8N.
        timeout: Timeout en segundos (default 10).
    """

    def __init__(self, webhook_url: str, timeout: int = 10) -> None:
        self.webhook_url = webhook_url
        self.timeout = timeout

    async def send(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
    ) -> None:
        """Envía un mensaje vía el webhook de N8N.

        Args:
            destinatario: Email descifrado del destinatario (SOLO en memoria).
            asunto: Asunto del email.
            cuerpo: Cuerpo del email.

        Raises:
            N8NTimeoutError: Si el webhook no responde en `self.timeout` segundos.
            N8NError: Si el webhook devuelve un error HTTP.
        """
        payload: dict[str, Any] = {
            "destinatario": destinatario,
            "asunto": asunto,
            "cuerpo": cuerpo,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.webhook_url, json=payload)
        except httpx.TimeoutException as exc:
            logger.warning(
                "n8n_client_timeout",
                extra={
                    "event": "n8n_timeout",
                    "timeout_seconds": self.timeout,
                    "detail": str(exc),
                },
            )
            raise N8NTimeoutError(self.timeout) from exc
        except httpx.RequestError as exc:
            logger.error(
                "n8n_client_request_error",
                extra={
                    "event": "n8n_request_error",
                    "detail": str(exc),
                },
            )
            raise N8NError(0, str(exc)) from exc

        if response.status_code >= 400:
            detail = response.text[:500] if response.text else "no body"
            logger.error(
                "n8n_client_http_error",
                extra={
                    "event": "n8n_http_error",
                    "status_code": response.status_code,
                    "detail": detail,
                },
            )
            raise N8NError(response.status_code, detail)

        logger.debug(
            "n8n_client_send_ok",
            extra={
                "event": "n8n_send_ok",
                "status_code": response.status_code,
            },
        )
