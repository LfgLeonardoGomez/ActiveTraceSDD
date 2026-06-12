"""Tests Phase 6 — Wiring: main.py router registration (C-20)."""

import pytest


class TestMainPyRegistersC20Routers:
    """T-13 RED → GREEN: main.py includes perfil and inbox routers."""

    @pytest.mark.asyncio
    async def test_perfil_router_registered(self):
        from app.main import app
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert any("/api/v1/perfil" in str(p) for p in routes)

    @pytest.mark.asyncio
    async def test_inbox_router_registered(self):
        from app.main import app
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert any("/api/v1/inbox" in str(p) for p in routes)
