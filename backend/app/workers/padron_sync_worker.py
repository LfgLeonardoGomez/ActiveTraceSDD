"""Worker de sync nocturna del padrón desde Moodle WS (C-09 Tasks 8.1-8.3).

Itera tenants con moodle_url configurada y ejecuta confirm_import para
cada combinación materia/cohorte que tenga course_id asociado.

Skip silencioso: tenant sin moodle_url → no genera llamadas HTTP.
MoodleWSError → log de error + continúa con el siguiente tenant.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.integrations.moodle_ws import MoodleWSClient, MoodleWSError
from app.services.padron_service import PadronService

logger = logging.getLogger(__name__)


@dataclass
class PadronSyncConfig:
    """Combinación materia×cohorte×course_id que debe sincronizarse."""
    tenant_id: Any
    materia_id: Any
    cohorte_id: Any
    course_id: str


class PadronSyncWorker:
    """Ejecuta la sync periódica de padrón desde Moodle para todos los tenants."""

    async def run_once(
        self,
        *,
        tenants: list[Any],
        sync_configs: list[Any],
        db_session: Any = None,
    ) -> None:
        """Ejecuta una pasada completa de sync para todos los tenants configurados."""
        for tenant in tenants:
            moodle_url = getattr(tenant, "moodle_url", None)
            moodle_token = getattr(tenant, "moodle_token", None)

            if not moodle_url:
                # Skip silencioso — no loggear ni generar llamadas HTTP
                continue

            tenant_configs = [
                c for c in sync_configs if str(c.tenant_id) == str(tenant.id)
            ]

            for cfg in tenant_configs:
                await self._sync_one(
                    tenant=tenant,
                    cfg=cfg,
                    moodle_url=moodle_url,
                    moodle_token=moodle_token or "",
                    db_session=db_session,
                )

    async def _sync_one(
        self,
        *,
        tenant: Any,
        cfg: Any,
        moodle_url: str,
        moodle_token: str,
        db_session: Any,
    ) -> None:
        try:
            client = MoodleWSClient(moodle_url, moodle_token)
            rows = await client.get_padron_rows(cfg.course_id)
        except MoodleWSError as exc:
            logger.error(
                "padron_sync_worker_error",
                extra={
                    "event": "moodle_ws_error",
                    "tenant_id": str(tenant.id),
                    "course_id": cfg.course_id,
                    "retry_after": exc.retry_after,
                    "detail": str(exc),
                },
            )
            return

        svc = PadronService(db_session, tenant.id)
        try:
            await svc.confirm_import(
                rows=rows,
                materia_id=cfg.materia_id,
                cohorte_id=cfg.cohorte_id,
                cargado_por_id=None,
                origen="moodle_ws",
                ip=None,
                user_agent="padron-sync-worker",
            )
        except Exception as exc:
            logger.error(
                "padron_sync_worker_error",
                extra={
                    "event": "confirm_import_error",
                    "tenant_id": str(tenant.id),
                    "detail": str(exc),
                },
            )
