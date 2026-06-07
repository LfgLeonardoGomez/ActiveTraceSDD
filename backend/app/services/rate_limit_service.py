"""Servicio de rate limiting.

Clave: resource = f"{endpoint}:{ip}:{email}".
Ventana: tiempo dividido en bloques de N segundos.
"""

from datetime import datetime, timezone

from app.repositories.rate_limit_repository import RateLimitRepository


class RateLimitService:
    """Servicio de rate limiting por PostgreSQL."""

    def __init__(self, rate_limit_repo: RateLimitRepository) -> None:
        self.rate_limit_repo = rate_limit_repo

    def build_resource_key(
        self,
        endpoint: str,
        ip_address: str,
        identifier: str,
    ) -> str:
        """Normaliza la clave de rate limiting."""
        return f"{endpoint}:{ip_address}:{identifier.lower()}"

    async def check_limit(
        self,
        resource: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """Verifica si un recurso excede el limite.

        Returns:
            (permitido: bool, retry_after: int)
            retry_after = segundos restantes hasta fin de ventana.
        """
        now = datetime.now(timezone.utc)
        # Alinear a ventana fija
        epoch_seconds = int(now.timestamp())
        window_start_epoch = (epoch_seconds // window_seconds) * window_seconds
        window_start = datetime.fromtimestamp(window_start_epoch, tz=timezone.utc)
        next_window = window_start_epoch + window_seconds
        retry_after = next_window - epoch_seconds

        count = await self.rate_limit_repo.increment(resource, window_start)
        permitted = count <= max_requests
        return permitted, retry_after
