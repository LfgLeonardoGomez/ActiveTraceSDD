"""Utilidad de cifrado AES-256-GCM para PII en reposo.

Cifra texto plano usando AES-256-GCM con nonce aleatorio de 12 bytes.
El resultado es una cadena base64 que incluye: nonce (12 bytes) +
authentication tag (16 bytes) + ciphertext.

Descifrado valida integridad (tamper detection) y falla con EncryptionError
si el ciphertext fue modificado.
"""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings

settings = Settings()


class EncryptionError(Exception):
    """Error de cifrado/descifrado (integridad comprometida, clave inválida, etc.)."""

    pass


# Constantes de formato
NONCE_LENGTH = 12  # bytes recomendados para GCM
TAG_LENGTH = 16    # bytes (128 bits)


def _get_key() -> bytes:
    """Devuelve la clave de 32 bytes desde Settings."""
    key = settings.encryption_key.encode("utf-8")
    if len(key) != 32:
        raise EncryptionError("ENCRYPTION_KEY must be exactly 32 bytes")
    return key


def encrypt_pii(plain_text: str) -> str:
    """Cifra texto plano con AES-256-GCM.

    Args:
        plain_text: Texto a cifrar.

    Returns:
        Cadena base64 que contiene nonce + tag + ciphertext.
    """
    key = _get_key()
    nonce = os.urandom(NONCE_LENGTH)
    aesgcm = AESGCM(key)
    cipher_bytes = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
    # cipher_bytes = ciphertext + tag (16 bytes al final)
    # prefixamos nonce para almacenamiento autónomo
    payload = nonce + cipher_bytes
    return base64.b64encode(payload).decode("ascii")


def decrypt_pii(cipher_text: str) -> str:
    """Descifra texto cifrado con AES-256-GCM.

    Args:
        cipher_text: Cadena base64 con nonce + tag + ciphertext.

    Returns:
        Texto plano original.

    Raises:
        EncryptionError: Si el ciphertext es inválido, corrupto o fue modificado.
    """
    try:
        payload = base64.b64decode(cipher_text)
    except Exception as exc:
        raise EncryptionError("Invalid base64 encoding") from exc

    if len(payload) < NONCE_LENGTH + TAG_LENGTH:
        raise EncryptionError("Ciphertext too short")

    nonce = payload[:NONCE_LENGTH]
    cipher_bytes = payload[NONCE_LENGTH:]
    key = _get_key()
    aesgcm = AESGCM(key)

    try:
        plain_bytes = aesgcm.decrypt(nonce, cipher_bytes, None)
    except Exception as exc:
        raise EncryptionError("Tamper detected or corrupted ciphertext") from exc

    return plain_bytes.decode("utf-8")
