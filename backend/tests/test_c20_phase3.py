"""Tests Phase 3 — Repository: MensajeRepository (C-20)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4


class TestMensajeRepositoryImport:
    """T-06 RED → GREEN: MensajeRepository exists."""

    @pytest.mark.asyncio
    async def test_mensaje_repository_import(self):
        from app.repositories.mensaje_repository import MensajeRepository
        assert MensajeRepository is not None
