"""Servicio de 2FA TOTP: enroll, verificacion, backup codes.

Usa pyotp para generar/validar TOTP y AES-256 para cifrar el secreto.
"""

import base64
import hashlib
import hmac
import secrets
from io import BytesIO

import pyotp
import qrcode
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.models.user import Usuario
from app.repositories.two_factor_repository import TwoFactorRepository


class TwoFactorService:
    """Servicio de gestion de 2FA TOTP."""

    def __init__(
        self,
        db_session: AsyncSession,
        two_factor_repo: TwoFactorRepository,
    ) -> None:
        self.db_session = db_session
        self.two_factor_repo = two_factor_repo

    async def enroll(self, user: Usuario) -> dict:
        """Genera secreto TOTP, lo cifra y retorna QR + URI.

        Returns:
            dict con provisioning_uri y qr_base64.
        """
        raw_secret = pyotp.random_base32()
        encrypted = security.encrypt_aes256(raw_secret)
        await self.two_factor_repo.update_secret(user.id, encrypted)

        totp = pyotp.TOTP(raw_secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="activia-trace",
        )

        qr = qrcode.make(provisioning_uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("ascii")

        return {
            "provisioning_uri": provisioning_uri,
            "qr_base64": qr_base64,
        }

    async def confirm_enroll(self, user: Usuario, code: str) -> list[str]:
        """Valida codigo TOTP y activa 2FA.

        Returns:
            Lista de 10 backup codes (strings de 8 chars).

        Raises:
            ValueError: si el codigo es invalido.
        """
        enrollment = await self.two_factor_repo.get_active_for_user(user.id)
        if enrollment is None:
            raise ValueError("No pending enrollment")

        raw_secret = security.decrypt_aes256(enrollment.encrypted_secret)
        totp = pyotp.TOTP(raw_secret)
        if not totp.verify(code, valid_window=1):
            raise ValueError("Invalid TOTP code")

        await self.two_factor_repo.confirm(user.id)
        user.is_2fa_enabled = True

        # Generar 10 backup codes y almacenar sus hashes
        backup_codes = [
            secrets.token_urlsafe(6)[:8].upper() for _ in range(10)
        ]
        code_hashes = [
            hashlib.sha256(c.encode("utf-8")).hexdigest() for c in backup_codes
        ]
        enrollment.backup_code_hashes = code_hashes

        await self.db_session.commit()
        return backup_codes

    async def verify_totp(self, user: Usuario, code: str) -> bool:
        """Verifica un codigo TOTP contra el secreto almacenado."""
        if not user.is_2fa_enabled:
            return False
        enrollment = await self.two_factor_repo.get_active_for_user(user.id)
        if enrollment is None:
            return False
        raw_secret = security.decrypt_aes256(enrollment.encrypted_secret)
        totp = pyotp.TOTP(raw_secret)
        return totp.verify(code, valid_window=1)

    async def verify_backup_code(self, user: Usuario, code: str) -> bool:
        """Verifica un backup code y lo marca como usado.

        Raises:
            ValueError: si no hay backup codes o ya fue usado.
        """
        enrollment = await self.two_factor_repo.get_active_for_user(user.id)
        if enrollment is None or not enrollment.backup_code_hashes:
            return False

        code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
        remaining_hashes = []
        found = False
        for stored_hash in enrollment.backup_code_hashes:
            if hmac.compare_digest(code_hash, stored_hash) and not found:
                found = True
                continue
            remaining_hashes.append(stored_hash)

        if not found:
            return False

        enrollment.backup_code_hashes = remaining_hashes if remaining_hashes else None
        await self.db_session.commit()
        return True

    async def disable_2fa(self, user: Usuario, code: str) -> None:
        """Deshabilita 2FA previa verificacion de TOTP."""
        if not await self.verify_totp(user, code):
            raise ValueError("Invalid TOTP code")
        await self.two_factor_repo.soft_delete_for_user(user.id)
        user.is_2fa_enabled = False
        await self.db_session.commit()
