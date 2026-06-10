"""Repositorio del padrón de alumnos versionado (C-09).

Cifrado/descifrado de email en EntradaPadron ocurre SOLO en esta capa:
- Al escribir: encrypt_pii(email) antes de persistir.
- Al leer: decrypt_pii(email) después de leer.
- El service trabaja SIEMPRE con texto plano.

Todas las queries filtran por tenant_id (BaseRepository garantiza esto).
Vaciar es scope-isolated: solo afecta versiones con cargado_por = actor.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_pii, encrypt_pii
from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.base import BaseRepository


class PadronRepository(BaseRepository[VersionPadron]):
    """Repositorio de VersionPadron con operaciones de gestión de padrón.

    Hereda scope de tenant del BaseRepository.
    Maneja cifrado transparente del email de EntradaPadron.
    """

    def __init__(self, db_session: AsyncSession, tenant_id: UUID) -> None:
        super().__init__(db_session, VersionPadron, tenant_id)

    # ------------------------------------------------------------------
    # VersionPadron
    # ------------------------------------------------------------------

    async def crear_version(
        self,
        *,
        materia_id: UUID,
        cohorte_id: UUID,
        cargado_por: UUID | None = None,
        origen: str = "manual",
    ) -> VersionPadron:
        """Crea una nueva VersionPadron en estado inactivo (activa=False).

        La activación se hace explícitamente con activar_version().
        """
        version = VersionPadron(
            tenant_id=self.tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=cargado_por,
            cargado_at=datetime.now(timezone.utc),
            activa=False,
            origen=origen,
        )
        self.db_session.add(version)
        await self.db_session.commit()
        await self.db_session.refresh(version)
        return version

    async def get_active_version(
        self, materia_id: UUID, cohorte_id: UUID
    ) -> VersionPadron | None:
        """Devuelve la versión activa del padrón para materia × cohorte, o None."""
        query = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.cohorte_id == cohorte_id,
                VersionPadron.activa.is_(True),
                VersionPadron.deleted_at.is_(None),
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def activar_version(
        self, new_version_id: UUID, materia_id: UUID, cohorte_id: UUID
    ) -> VersionPadron:
        """Activa una versión y desactiva la anterior en una transacción atómica.

        Garantiza que solo haya UNA versión activa por (tenant_id, materia_id, cohorte_id).
        La versión anterior NO se borra — solo se marca activa=False (historial preservado).
        """
        # Desactivar todas las versiones activas previas para este scope
        await self.db_session.execute(
            update(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.cohorte_id == cohorte_id,
                VersionPadron.activa.is_(True),
                VersionPadron.id != new_version_id,
                VersionPadron.deleted_at.is_(None),
            )
            .values(activa=False, updated_at=datetime.now(timezone.utc))
        )

        # Activar la nueva versión
        await self.db_session.execute(
            update(VersionPadron)
            .where(
                VersionPadron.id == new_version_id,
                VersionPadron.tenant_id == self.tenant_id,
            )
            .values(activa=True, updated_at=datetime.now(timezone.utc))
        )

        await self.db_session.commit()

        query = select(VersionPadron).where(VersionPadron.id == new_version_id)
        result = await self.db_session.execute(query)
        return result.scalar_one()

    async def soft_delete_all_versions(
        self, *, materia_id: UUID, cargado_por: UUID
    ) -> int:
        """Soft delete de todas las versiones del padrón en el scope (cargado_por × materia).

        Scope-isolated (RN-04): solo elimina versiones cargadas POR el usuario actor.
        También marca como deleted todas las EntradaPadron de esas versiones.

        Returns:
            Número de versiones marcadas como eliminadas.
        """
        now = datetime.now(timezone.utc)

        # Buscar versiones del scope
        q = select(VersionPadron).where(
            VersionPadron.tenant_id == self.tenant_id,
            VersionPadron.materia_id == materia_id,
            VersionPadron.cargado_por == cargado_por,
            VersionPadron.deleted_at.is_(None),
        )
        result = await self.db_session.execute(q)
        versiones = result.scalars().all()

        if not versiones:
            return 0

        version_ids = [v.id for v in versiones]

        # Soft delete de entradas de esas versiones
        await self.db_session.execute(
            update(EntradaPadron)
            .where(
                EntradaPadron.version_id.in_(version_ids),
                EntradaPadron.tenant_id == self.tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
            .values(deleted_at=now, updated_at=now)
        )

        # Soft delete de las versiones
        await self.db_session.execute(
            update(VersionPadron)
            .where(
                VersionPadron.id.in_(version_ids),
                VersionPadron.tenant_id == self.tenant_id,
            )
            .values(deleted_at=now, updated_at=now)
        )

        await self.db_session.commit()
        return len(versiones)

    # ------------------------------------------------------------------
    # EntradaPadron — cifrado transparente
    # ------------------------------------------------------------------

    def _decrypt_entrada(self, entrada: EntradaPadron) -> EntradaPadron:
        """Descifra el email de una EntradaPadron in-place."""
        try:
            entrada.email = decrypt_pii(entrada.email)
        except Exception:
            pass
        return entrada

    async def crear_entrada(
        self,
        *,
        version_id: UUID,
        nombre: str,
        apellidos: str,
        email: str,
        comision: str = "",
        regional: str = "",
        usuario_id: UUID | None = None,
    ) -> EntradaPadron:
        """Crea una EntradaPadron cifrando el email antes de persistir."""
        entrada = EntradaPadron(
            tenant_id=self.tenant_id,
            version_id=version_id,
            usuario_id=usuario_id,
            nombre=nombre,
            apellidos=apellidos,
            email=encrypt_pii(email),
            comision=comision,
            regional=regional,
        )
        self.db_session.add(entrada)
        await self.db_session.flush()
        await self.db_session.refresh(entrada)
        return self._decrypt_entrada(entrada)

    async def bulk_crear_entradas(
        self,
        version_id: UUID,
        entradas: list[dict],
    ) -> int:
        """Crea múltiples EntradaPadron en batch. Cada dict debe incluir
        nombre, apellidos, email (plano), comision, regional, usuario_id.

        Returns:
            Número de entradas creadas.
        """
        objs = []
        for row in entradas:
            objs.append(
                EntradaPadron(
                    tenant_id=self.tenant_id,
                    version_id=version_id,
                    usuario_id=row.get("usuario_id"),
                    nombre=row["nombre"],
                    apellidos=row["apellidos"],
                    email=encrypt_pii(row["email"]),
                    comision=row.get("comision", ""),
                    regional=row.get("regional", ""),
                )
            )
        self.db_session.add_all(objs)
        await self.db_session.flush()
        return len(objs)

    async def get_entradas_by_version(
        self, version_id: UUID
    ) -> list[EntradaPadron]:
        """Lista todas las EntradaPadron de una versión con email descifrado."""
        query = select(EntradaPadron).where(
            EntradaPadron.version_id == version_id,
            EntradaPadron.tenant_id == self.tenant_id,
            EntradaPadron.deleted_at.is_(None),
        )
        result = await self.db_session.execute(query)
        entradas = result.scalars().all()
        return [self._decrypt_entrada(e) for e in entradas]
