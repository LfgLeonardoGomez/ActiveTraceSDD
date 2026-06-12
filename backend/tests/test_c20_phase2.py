"""Tests Phase 2 — Schemas: PerfilUpdate, Mensaje schemas (C-20)."""

import pytest
from datetime import datetime
from uuid import uuid4


class TestPerfilUpdateSchema:
    """T-04 RED → GREEN: PerfilUpdate schema validates correctly."""

    @pytest.mark.asyncio
    async def test_perfil_update_import(self):
        from app.schemas.perfil import PerfilUpdate
        assert PerfilUpdate is not None

    @pytest.mark.asyncio
    async def test_perfil_update_accepts_valid_fields(self):
        from app.schemas.perfil import PerfilUpdate
        data = PerfilUpdate(nombre="Juan", apellidos="Pérez", banco="BBVA")
        assert data.nombre == "Juan"
        assert data.apellidos == "Pérez"
        assert data.banco == "BBVA"

    @pytest.mark.asyncio
    async def test_perfil_update_rejects_cuil(self):
        from pydantic import ValidationError
        from app.schemas.perfil import PerfilUpdate
        with pytest.raises(ValidationError) as exc_info:
            PerfilUpdate(cuil="20-12345678-9")
        assert "cuil" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_perfil_update_rejects_unknown_field(self):
        from pydantic import ValidationError
        from app.schemas.perfil import PerfilUpdate
        with pytest.raises(ValidationError) as exc_info:
            PerfilUpdate(extra_field="bad")
        assert "extra_field" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_perfil_read_import(self):
        from app.schemas.perfil import PerfilRead
        assert PerfilRead is not None


class TestMensajeSchemas:
    """T-05 RED → GREEN: Mensaje schemas validate correctly."""

    @pytest.mark.asyncio
    async def test_mensaje_schemas_import(self):
        from app.schemas.mensajes import MensajeRead, InboxThreadRead, InboxThreadDetailRead, MensajeReplyCreate
        assert MensajeRead is not None
        assert InboxThreadRead is not None
        assert InboxThreadDetailRead is not None
        assert MensajeReplyCreate is not None

    @pytest.mark.asyncio
    async def test_mensaje_reply_create_requires_cuerpo(self):
        from pydantic import ValidationError
        from app.schemas.mensajes import MensajeReplyCreate
        with pytest.raises(ValidationError) as exc_info:
            MensajeReplyCreate()
        assert "cuerpo" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_mensaje_reply_create_accepts_optional_asunto(self):
        from app.schemas.mensajes import MensajeReplyCreate
        data = MensajeReplyCreate(cuerpo="Respuesta", asunto="Re: Hola")
        assert data.cuerpo == "Respuesta"
        assert data.asunto == "Re: Hola"

    @pytest.mark.asyncio
    async def test_mensaje_read_from_attributes(self):
        from app.schemas.mensajes import MensajeRead
        # MensajeRead should have from_attributes=True
        assert MensajeRead.model_config.get("from_attributes") is True

    @pytest.mark.asyncio
    async def test_inbox_thread_detail_has_replies(self):
        from app.schemas.mensajes import InboxThreadDetailRead
        fields = InboxThreadDetailRead.model_fields
        assert "replies" in fields
