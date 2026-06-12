"""Interfaz FileStoragePort (C-18, decisión D6).

El archivo de factura se persiste FUERA de PostgreSQL.
Factura.referencia_archivo es un string opaco que apunta al storage.
El binding concreto (S3, disco local, etc.) es configuración de infra.

El binding real a S3 será un change de infra posterior (C-23/C-24).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StoredFile:
    """Resultado del upload al storage."""

    referencia: str
    """Identificador opaco del archivo en el storage."""
    tamano_kb: float
    """Tamaño del archivo en kilobytes."""
    content_type: str | None = None


class FileStoragePort(ABC):
    """Puerto de almacenamiento de archivos (interfaz hexagonal).

    Implementaciones concretas:
    - LocalFileStorage (stub de dev — ver infrastructure/local_file_storage.py)
    - S3FileStorage (binding de producción, change futuro)
    """

    @abstractmethod
    async def upload(self, content: bytes, filename: str, content_type: str | None = None) -> StoredFile:
        """Sube un archivo y devuelve su referencia opaca + metadata.

        Args:
            content: Bytes del archivo.
            filename: Nombre original del archivo.
            content_type: MIME type opcional.

        Returns:
            StoredFile con referencia opaca y tamaño en KB.
        """
        ...

    @abstractmethod
    async def download(self, referencia: str) -> bytes:
        """Descarga un archivo por su referencia opaca.

        Args:
            referencia: Identificador opaco del archivo.

        Returns:
            Bytes del archivo.

        Raises:
            FileNotFoundError: Si la referencia no existe.
        """
        ...
