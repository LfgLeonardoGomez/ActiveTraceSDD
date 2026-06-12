"""Tests del FileStoragePort y LocalFileStorage (C-18, D6)."""

import pytest


@pytest.mark.asyncio
async def test_local_storage_upload():
    """Upload retorna referencia opaca con formato local://."""
    from app.modules.liquidaciones.infrastructure.local_file_storage import LocalFileStorage

    storage = LocalFileStorage()
    result = await storage.upload(b"contenido del archivo", "factura.pdf", "application/pdf")
    assert result.referencia.startswith("local://")
    assert "factura.pdf" in result.referencia
    assert result.tamano_kb > 0


@pytest.mark.asyncio
async def test_local_storage_download():
    """Download recupera exactamente el contenido subido."""
    from app.modules.liquidaciones.infrastructure.local_file_storage import LocalFileStorage

    storage = LocalFileStorage()
    content = b"contenido de test 12345"
    stored = await storage.upload(content, "test.pdf")
    downloaded = await storage.download(stored.referencia)
    assert downloaded == content


@pytest.mark.asyncio
async def test_local_storage_not_found():
    """Download de referencia inexistente → FileNotFoundError."""
    from app.modules.liquidaciones.infrastructure.local_file_storage import LocalFileStorage

    storage = LocalFileStorage()
    with pytest.raises(FileNotFoundError):
        await storage.download("local://no-existe/archivo.pdf")


@pytest.mark.asyncio
async def test_local_storage_tamano_kb():
    """tamano_kb calculado correctamente."""
    from app.modules.liquidaciones.infrastructure.local_file_storage import LocalFileStorage

    storage = LocalFileStorage()
    # 1024 bytes = 1 KB
    content = b"x" * 1024
    stored = await storage.upload(content, "test.txt")
    assert stored.tamano_kb == 1.0
