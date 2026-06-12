"""Tests Phase 5 — Routers: perfil.py, inbox.py (C-20)."""

import pytest


class TestPerfilRouter:
    """T-09 RED → GREEN: perfil router is importable and registered."""

    @pytest.mark.asyncio
    async def test_perfil_router_import(self):
        from app.api.v1.routers.perfil import router
        assert router is not None

    @pytest.mark.asyncio
    async def test_perfil_router_prefix(self):
        from app.api.v1.routers.perfil import router
        assert str(router.prefix) == "/api/v1/perfil"


class TestInboxRouter:
    """T-10 RED → GREEN: inbox router is importable and registered."""

    @pytest.mark.asyncio
    async def test_inbox_router_import(self):
        from app.api.v1.routers.inbox import router
        assert router is not None

    @pytest.mark.asyncio
    async def test_inbox_router_prefix(self):
        from app.api.v1.routers.inbox import router
        assert str(router.prefix) == "/api/v1/inbox"
