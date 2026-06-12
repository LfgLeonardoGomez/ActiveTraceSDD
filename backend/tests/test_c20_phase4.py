"""Tests Phase 4 — Services: PerfilService, MensajeService (C-20)."""

import pytest
from uuid import uuid4


class TestPerfilServiceImport:
    """T-07 RED → GREEN: PerfilService exists."""

    @pytest.mark.asyncio
    async def test_perfil_service_import(self):
        from app.services.perfil_service import PerfilService
        assert PerfilService is not None


class TestMensajeServiceImport:
    """T-08 RED → GREEN: MensajeService exists."""

    @pytest.mark.asyncio
    async def test_mensaje_service_import(self):
        from app.services.mensaje_service import MensajeService
        assert MensajeService is not None
