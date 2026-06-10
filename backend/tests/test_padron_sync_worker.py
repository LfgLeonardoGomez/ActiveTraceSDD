"""Tests del worker de sync nocturna de padrón (C-09 Tasks 8.1-8.4).

Escenarios cubiertos:
- tenant sin moodle_url → skip silencioso, sin llamadas HTTP
- tenant con moodle_url pero MoodleWSError → log de error, continúa
- tenant con moodle_url válido → sync exitosa
"""

from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from app.workers.padron_sync_worker import PadronSyncWorker


class _FakeTenant:
    def __init__(self, id, moodle_url=None, moodle_token=None):
        self.id = id
        self.moodle_url = moodle_url
        self.moodle_token = moodle_token


class _FakeSyncConfig:
    def __init__(self, tenant_id, materia_id, cohorte_id, course_id):
        self.tenant_id = tenant_id
        self.materia_id = materia_id
        self.cohorte_id = cohorte_id
        self.course_id = course_id


class TestPadronSyncWorkerSkipLogic:
    """Task 8.4: tenant sin Moodle no genera llamadas HTTP."""

    @pytest.mark.asyncio
    async def test_tenant_sin_moodle_url_no_genera_llamadas_http(self) -> None:
        """Tenant con moodle_url=None → skip sin tocar MoodleWSClient."""
        tenant_sin_moodle = _FakeTenant(id="tid-1", moodle_url=None)
        configs = [_FakeSyncConfig("tid-1", "mat-1", "coh-1", "course-1")]

        with patch(
            "app.workers.padron_sync_worker.MoodleWSClient"
        ) as MockClient:
            worker = PadronSyncWorker()
            await worker.run_once(
                tenants=[tenant_sin_moodle],
                sync_configs=configs,
            )

        MockClient.assert_not_called()

    @pytest.mark.asyncio
    async def test_tenant_con_moodle_url_vacia_no_genera_llamadas_http(
        self,
    ) -> None:
        """Triangulación: moodle_url vacío ("") → skip también."""
        tenant_vacio = _FakeTenant(id="tid-2", moodle_url="")
        configs = [_FakeSyncConfig("tid-2", "mat-2", "coh-2", "course-2")]

        with patch(
            "app.workers.padron_sync_worker.MoodleWSClient"
        ) as MockClient:
            worker = PadronSyncWorker()
            await worker.run_once(tenants=[tenant_vacio], sync_configs=configs)

        MockClient.assert_not_called()

    @pytest.mark.asyncio
    async def test_moodle_ws_error_loggea_y_continua(self) -> None:
        """MoodleWSError no detiene el worker — continúa con el siguiente tenant."""
        from app.integrations.moodle_ws import MoodleWSError

        tenant_a = _FakeTenant(id="tid-a", moodle_url="https://a.moodle.com", moodle_token="tok")
        tenant_b = _FakeTenant(id="tid-b", moodle_url="https://b.moodle.com", moodle_token="tok")

        configs = [
            _FakeSyncConfig("tid-a", "mat-a", "coh-a", "course-a"),
            _FakeSyncConfig("tid-b", "mat-b", "coh-b", "course-b"),
        ]

        mock_client_a = AsyncMock()
        mock_client_a.get_padron_rows = AsyncMock(
            side_effect=MoodleWSError("WS error", retry_after=60)
        )
        mock_client_b = AsyncMock()
        mock_client_b.get_padron_rows = AsyncMock(return_value=[])

        call_count = {"n": 0}

        def client_factory(url, token):
            call_count["n"] += 1
            if "a.moodle" in url:
                return mock_client_a
            return mock_client_b

        with (
            patch("app.workers.padron_sync_worker.MoodleWSClient", side_effect=client_factory),
            patch("app.workers.padron_sync_worker.PadronService") as MockService,
        ):
            mock_svc_instance = AsyncMock()
            mock_svc_instance.confirm_import = AsyncMock(return_value=MagicMock(id="v1"))
            MockService.return_value = mock_svc_instance

            worker = PadronSyncWorker()
            await worker.run_once(tenants=[tenant_a, tenant_b], sync_configs=configs)

        # El worker intentó ambos tenants (2 llamadas a factory)
        assert call_count["n"] == 2

    @pytest.mark.asyncio
    async def test_sync_exitosa_llama_confirm_import(self) -> None:
        """Tenant configurado → confirm_import ejecutado para cada config."""
        from app.schemas.padron import PadronImportRow

        tenant = _FakeTenant(id="tid-ok", moodle_url="https://moodle.ok", moodle_token="tok")
        configs = [_FakeSyncConfig("tid-ok", "mat-ok", "coh-ok", "course-ok")]

        fake_rows = [PadronImportRow(nombre="A", apellidos="B", email="a@b.com")]

        mock_client = AsyncMock()
        mock_client.get_padron_rows = AsyncMock(return_value=fake_rows)

        with (
            patch(
                "app.workers.padron_sync_worker.MoodleWSClient", return_value=mock_client
            ),
            patch("app.workers.padron_sync_worker.PadronService") as MockService,
        ):
            mock_svc_instance = AsyncMock()
            mock_svc_instance.confirm_import = AsyncMock(
                return_value=MagicMock(id="v-new")
            )
            MockService.return_value = mock_svc_instance

            worker = PadronSyncWorker()
            await worker.run_once(tenants=[tenant], sync_configs=configs)

        mock_svc_instance.confirm_import.assert_called_once()
        call_kwargs = mock_svc_instance.confirm_import.call_args.kwargs
        assert call_kwargs["rows"] == fake_rows
        assert call_kwargs["origen"] == "moodle_ws"
