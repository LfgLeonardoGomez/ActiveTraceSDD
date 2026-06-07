"""Tests de TDD para utilidad de cifrado AES-256 — C-02 Task Group 2."""

import pytest
import base64

from app.core.encryption import encrypt_pii, decrypt_pii, EncryptionError


class TestEncryption:
    """RED/GREEN/TRIANGULATE/REFACTOR para encrypt_pii / decrypt_pii."""

    def test_encrypt_pii_returns_base64(self):
        """RED: cifrar devuelve string base64 no vacío."""
        ciphertext = encrypt_pii("sensitive data")
        assert isinstance(ciphertext, str)
        assert len(ciphertext) > 0
        # Verificar que es base64 válido
        decoded = base64.b64decode(ciphertext)
        assert len(decoded) > 0

    def test_decrypt_pii_restores_plaintext(self):
        """RED: round-trip cifrar → descifrar devuelve texto original."""
        original = "john.doe@example.com"
        ciphertext = encrypt_pii(original)
        decrypted = decrypt_pii(ciphertext)
        assert decrypted == original

    def test_encrypt_is_non_deterministic(self):
        """TRIANGULATE: dos cifrados del mismo texto dan resultados distintos (nonce random)."""
        original = "same text"
        c1 = encrypt_pii(original)
        c2 = encrypt_pii(original)
        assert c1 != c2
        assert decrypt_pii(c1) == original
        assert decrypt_pii(c2) == original

    def test_decrypt_pii_different_lengths(self):
        """TRIANGULATE: round-trip para email, DNI, CBU."""
        test_cases = [
            ("email", "profesor.universidad@institucion.edu.ar"),
            ("dni", "12345678"),
            ("cbu", "0720049240000001234567"),
            ("cuil", "20-12345678-9"),
        ]
        for label, original in test_cases:
            ciphertext = encrypt_pii(original)
            decrypted = decrypt_pii(ciphertext)
            assert decrypted == original, f"Fallo round-trip para {label}"

    def test_tamper_detection_modifies_byte(self):
        """TRIANGULATE: modificar 1 byte del ciphertext falla descifrado."""
        original = "super secret"
        ciphertext = encrypt_pii(original)
        # Decodificar base64
        raw = bytearray(base64.b64decode(ciphertext))
        # Modificar un byte en el ciphertext (después de nonce+tag)
        raw[-1] ^= 0xFF
        tampered = base64.b64encode(bytes(raw)).decode("ascii")
        with pytest.raises(EncryptionError):
            decrypt_pii(tampered)

    def test_tamper_detection_truncates(self):
        """TRIANGULATE: truncar ciphertext falla descifrado."""
        original = "another secret"
        ciphertext = encrypt_pii(original)
        raw = base64.b64decode(ciphertext)
        truncated = base64.b64encode(raw[:-4]).decode("ascii")
        with pytest.raises(EncryptionError):
            decrypt_pii(truncated)

    def test_decrypt_pii_invalid_base64(self):
        """TRIANGULATE: base64 inválido falla descifrado."""
        with pytest.raises(EncryptionError):
            decrypt_pii("not-valid-base64!!!")

    def test_encrypt_pii_empty_string(self):
        """TRIANGULATE: cifrar string vacío funciona."""
        original = ""
        ciphertext = encrypt_pii(original)
        decrypted = decrypt_pii(ciphertext)
        assert decrypted == original

    def test_encryption_key_is_32_bytes(self):
        """TRIANGULATE: la clave de settings es exactamente 32 bytes."""
        from app.core.config import Settings
        settings = Settings()
        key_bytes = settings.encryption_key.encode("utf-8")
        assert len(key_bytes) == 32
