"""Stub local de FileStoragePort para desarrollo y tests (C-18, decisión D6).

Almacena archivos en memoria. NO usar en producción.
El binding real a S3/equivalente se implementa en un change futuro.
"""

import uuid

from app.modules.liquidaciones.domain.file_storage_port import FileStoragePort, StoredFile


class LocalFileStorage(FileStoragePort):
    """Implementación in-memory de FileStoragePort.

    Útil para desarrollo local y tests sin infraestructura de storage.
    Los archivos se pierden al reiniciar el proceso.
    """

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    async def upload(self, content: bytes, filename: str, content_type: str | None = None) -> StoredFile:
        """Guarda en memoria y devuelve referencia tipo local://<uuid>/<filename>."""
        ref_id = str(uuid.uuid4())
        referencia = f"local://{ref_id}/{filename}"
        self._store[referencia] = content
        tamano_kb = len(content) / 1024.0
        return StoredFile(
            referencia=referencia,
            tamano_kb=round(tamano_kb, 2),
            content_type=content_type,
        )

    async def download(self, referencia: str) -> bytes:
        """Recupera el archivo por su referencia.

        Raises:
            FileNotFoundError: Si la referencia no existe en el store local.
        """
        if referencia not in self._store:
            raise FileNotFoundError(f"Archivo no encontrado: {referencia}")
        return self._store[referencia]
