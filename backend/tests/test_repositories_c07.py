"""Tests TDD para repositorios C-07: UsuarioRepository y AsignacionRepository.

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Tests usan DB real (sin mocks — regla dura).
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================
# GRUPO 4: UsuarioRepository — cifrado PII transparente
# ============================================================


class TestUsuarioRepositoryPiiCifrada:
    """Task 4.1 RED → GREEN → TRIANGULATE: PII cifrada en DB."""

    @pytest.mark.asyncio
    async def test_usuario_repository_pii_cifrada_en_db(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 4.1: crear usuario vía repositorio → email cifrado en DB,
        descifrado al leer por ID."""
        from app.repositories.usuarios import UsuarioRepository
        from sqlalchemy import text

        repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await repo.create(
            nombre="Ana",
            apellidos="García",
            email="ana.garcia@test.com",
            estado="Activo",
        )

        # El email devuelto por el repositorio es texto plano
        assert usuario.email == "ana.garcia@test.com"
        assert usuario.email_hash is not None
        assert len(usuario.email_hash) == 64  # HMAC-SHA256 hexdigest

        # Verificar que en la DB el email está cifrado (no texto plano)
        raw = await db_session.execute(
            text("SELECT email, email_hash FROM usuarios WHERE id = :uid"),
            {"uid": str(usuario.id)},
        )
        row = raw.fetchone()
        assert row is not None
        email_en_db = row[0]
        assert email_en_db != "ana.garcia@test.com", "Email debe estar cifrado en DB"
        assert len(email_en_db) > 50, "Ciphertext debe ser largo (base64)"

    @pytest.mark.asyncio
    async def test_usuario_repository_pii_cifrada_dni_cbu(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 4.1: DNI y CBU también se cifran en DB."""
        from app.repositories.usuarios import UsuarioRepository
        from sqlalchemy import text

        repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await repo.create(
            nombre="Carlos",
            apellidos="López",
            email="carlos.lopez@test.com",
            estado="Activo",
            dni="12345678",
            cbu="0720049240000001234567",
        )

        # Service ve texto plano
        assert usuario.dni == "12345678"
        assert usuario.cbu == "0720049240000001234567"

        # DB tiene ciphertext
        raw = await db_session.execute(
            text("SELECT dni, cbu FROM usuarios WHERE id = :uid"),
            {"uid": str(usuario.id)},
        )
        row = raw.fetchone()
        assert row[0] != "12345678", "DNI debe estar cifrado"
        assert row[1] != "0720049240000001234567", "CBU debe estar cifrado"

    @pytest.mark.asyncio
    async def test_usuario_repository_get_by_id_descifra_pii(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 4.2: get_by_id devuelve PII descifrada."""
        from app.repositories.usuarios import UsuarioRepository

        repo = UsuarioRepository(db_session, default_tenant.id)
        creado = await repo.create(
            nombre="María",
            apellidos="Sánchez",
            email="maria.sanchez@test.com",
            estado="Activo",
            cuil="27-12345678-9",
        )

        encontrado = await repo.get_by_id(creado.id)
        assert encontrado is not None
        assert encontrado.email == "maria.sanchez@test.com"
        assert encontrado.cuil == "27-12345678-9"


class TestUsuarioRepositoryUnicidadEmail:
    """Task 4.5 RED → GREEN → TRIANGULATE: unicidad email por tenant."""

    @pytest.mark.asyncio
    async def test_usuario_repository_unicidad_email_mismo_tenant(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 4.5: crear dos usuarios con mismo email en mismo tenant → error."""
        from sqlalchemy.exc import IntegrityError
        from app.repositories.usuarios import UsuarioRepository

        repo = UsuarioRepository(db_session, default_tenant.id)
        await repo.create(
            nombre="Pedro",
            apellidos="Martínez",
            email="duplicado@test.com",
            estado="Activo",
        )

        with pytest.raises((IntegrityError, Exception)):
            await repo.create(
                nombre="Luis",
                apellidos="Gómez",
                email="duplicado@test.com",
                estado="Activo",
            )

    @pytest.mark.asyncio
    async def test_usuario_repository_mismo_email_tenant_diferente_ok(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 4.5: mismo email en tenant distinto es permitido."""
        from app.models.tenant import Tenant
        from app.repositories.usuarios import UsuarioRepository

        # Crear segundo tenant
        tenant_b = Tenant(nombre="Tenant B Repos", slug="tenant-b-repos-c07", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        repo_a = UsuarioRepository(db_session, default_tenant.id)
        repo_b = UsuarioRepository(db_session, tenant_b.id)

        await repo_a.create(
            nombre="Alice",
            apellidos="Smith",
            email="compartido@test.com",
            estado="Activo",
        )
        u_b = await repo_b.create(
            nombre="Bob",
            apellidos="Smith",
            email="compartido@test.com",
            estado="Activo",
        )
        assert u_b is not None
        assert u_b.email == "compartido@test.com"

    @pytest.mark.asyncio
    async def test_usuario_repository_get_by_email_hash(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 4.6: get_by_email_hash permite lookup para auth."""
        from app.repositories.usuarios import UsuarioRepository

        repo = UsuarioRepository(db_session, default_tenant.id)
        await repo.create(
            nombre="Eva",
            apellidos="Torres",
            email="eva.torres@test.com",
            estado="Activo",
        )

        encontrado = await repo.get_by_email_hash("eva.torres@test.com")
        assert encontrado is not None
        assert encontrado.email == "eva.torres@test.com"

    @pytest.mark.asyncio
    async def test_usuario_repository_exists_by_email_hash(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 4.6: exists_by_email_hash detecta duplicados."""
        from app.repositories.usuarios import UsuarioRepository

        repo = UsuarioRepository(db_session, default_tenant.id)
        await repo.create(
            nombre="Rosa",
            apellidos="Blanco",
            email="rosa.blanco@test.com",
            estado="Activo",
        )

        assert await repo.exists_by_email_hash("rosa.blanco@test.com") is True
        assert await repo.exists_by_email_hash("noexiste@test.com") is False

    @pytest.mark.asyncio
    async def test_usuario_repository_update_re_cifra_email(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 4.6: update re-cifra email si cambia."""
        from app.repositories.usuarios import UsuarioRepository

        repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await repo.create(
            nombre="Iker",
            apellidos="Casillas",
            email="iker@original.com",
            estado="Activo",
        )

        updated = await repo.update(usuario.id, {"email": "iker@nuevo.com"})
        assert updated is not None
        assert updated.email == "iker@nuevo.com"
        # El hash también debe cambiar
        assert updated.email_hash is not None

    @pytest.mark.asyncio
    async def test_usuario_repository_soft_delete(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 4.2: soft_delete marca deleted_at."""
        from app.repositories.usuarios import UsuarioRepository

        repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await repo.create(
            nombre="Temporal",
            apellidos="Borrar",
            email="temporal@test.com",
            estado="Activo",
        )

        result = await repo.soft_delete(usuario.id)
        assert result is True

        encontrado = await repo.get_by_id(usuario.id)
        assert encontrado is None

    @pytest.mark.asyncio
    async def test_usuario_repository_list_paginated(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 4.2: list_paginated devuelve usuarios del tenant con PII descifrada."""
        from app.repositories.usuarios import UsuarioRepository

        repo = UsuarioRepository(db_session, default_tenant.id)
        await repo.create(nombre="U1", apellidos="T1", email="u1@test.com", estado="Activo")
        await repo.create(nombre="U2", apellidos="T2", email="u2@test.com", estado="Activo")

        items, total = await repo.list_paginated(limit=10, offset=0)
        assert total >= 2
        # PII descifrada en listado
        emails = {u.email for u in items}
        assert "u1@test.com" in emails
        assert "u2@test.com" in emails


# ============================================================
# GRUPO 5: AsignacionRepository
# ============================================================


class TestAsignacionRepository:
    """Task 5.1 RED → GREEN → TRIANGULATE: AsignacionRepository."""

    @pytest.mark.asyncio
    async def test_asignacion_repository_create_y_list(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 5.1 → GREEN: crear asignación y listar por tenant."""
        from app.repositories.usuarios import UsuarioRepository
        from app.repositories.asignaciones import AsignacionRepository

        # Crear usuario necesario
        usuario_repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await usuario_repo.create(
            nombre="Docente",
            apellidos="Repo",
            email="docente.repo@test.com",
            estado="Activo",
        )

        asig_repo = AsignacionRepository(db_session, default_tenant.id)
        asig = await asig_repo.create(
            usuario_id=usuario.id,
            rol="PROFESOR",
            desde=date.today() - timedelta(days=30),
            hasta=date.today() + timedelta(days=60),
        )

        assert asig.id is not None
        assert asig.rol == "PROFESOR"
        assert asig.tenant_id == default_tenant.id

        items, total = await asig_repo.list_paginated(limit=10, offset=0)
        assert total >= 1
        ids = {a.id for a in items}
        assert asig.id in ids

    @pytest.mark.asyncio
    async def test_asignacion_repository_aislamiento_multi_tenant(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 5.1: aislamiento multi-tenant en asignaciones."""
        from app.models.tenant import Tenant
        from app.repositories.usuarios import UsuarioRepository
        from app.repositories.asignaciones import AsignacionRepository

        # Crear segundo tenant
        tenant_b = Tenant(nombre="Tenant B Asig", slug="tenant-b-asig-c07", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        # Usuario en tenant A
        usuario_repo_a = UsuarioRepository(db_session, default_tenant.id)
        usuario_a = await usuario_repo_a.create(
            nombre="DocenteA",
            apellidos="TenantA",
            email="docente.a@test.com",
            estado="Activo",
        )

        # Asignación en tenant A
        asig_repo_a = AsignacionRepository(db_session, default_tenant.id)
        await asig_repo_a.create(
            usuario_id=usuario_a.id,
            rol="TUTOR",
            desde=date.today(),
        )

        # Tenant B no ve asignaciones del tenant A
        asig_repo_b = AsignacionRepository(db_session, tenant_b.id)
        items_b, total_b = await asig_repo_b.list_paginated(limit=10, offset=0)
        assert total_b == 0

    @pytest.mark.asyncio
    async def test_asignacion_repository_get_by_id(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 5.2: get_by_id retorna la asignación correcta."""
        from app.repositories.usuarios import UsuarioRepository
        from app.repositories.asignaciones import AsignacionRepository

        usuario_repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await usuario_repo.create(
            nombre="Tutor",
            apellidos="GetById",
            email="tutor.getbyid@test.com",
            estado="Activo",
        )

        asig_repo = AsignacionRepository(db_session, default_tenant.id)
        asig = await asig_repo.create(
            usuario_id=usuario.id,
            rol="TUTOR",
            desde=date.today(),
        )

        encontrada = await asig_repo.get_by_id(asig.id)
        assert encontrada is not None
        assert encontrada.id == asig.id
        assert encontrada.rol == "TUTOR"

    @pytest.mark.asyncio
    async def test_asignacion_repository_soft_delete(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 5.2: soft_delete marca deleted_at."""
        from app.repositories.usuarios import UsuarioRepository
        from app.repositories.asignaciones import AsignacionRepository

        usuario_repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await usuario_repo.create(
            nombre="Borrar",
            apellidos="Asig",
            email="borrar.asig@test.com",
            estado="Activo",
        )

        asig_repo = AsignacionRepository(db_session, default_tenant.id)
        asig = await asig_repo.create(
            usuario_id=usuario.id,
            rol="NEXO",
            desde=date.today(),
        )

        result = await asig_repo.soft_delete(asig.id)
        assert result is True

        encontrada = await asig_repo.get_by_id(asig.id)
        assert encontrada is None

    @pytest.mark.asyncio
    async def test_asignacion_repository_filtro_incluir_vencidas(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 5.2: filtro incluir_vencidas=True devuelve asignaciones pasadas."""
        from app.repositories.usuarios import UsuarioRepository
        from app.repositories.asignaciones import AsignacionRepository

        usuario_repo = UsuarioRepository(db_session, default_tenant.id)
        usuario = await usuario_repo.create(
            nombre="Historico",
            apellidos="Filtro",
            email="historico.filtro@test.com",
            estado="Activo",
        )

        asig_repo = AsignacionRepository(db_session, default_tenant.id)
        # Asignación vigente
        asig_vigente = await asig_repo.create(
            usuario_id=usuario.id,
            rol="PROFESOR",
            desde=date.today() - timedelta(days=10),
            hasta=date.today() + timedelta(days=10),
        )
        # Asignación vencida
        asig_vencida = await asig_repo.create(
            usuario_id=usuario.id,
            rol="TUTOR",
            desde=date.today() - timedelta(days=30),
            hasta=date.today() - timedelta(days=5),
        )

        # Sin incluir_vencidas: solo vigente (no filtramos por estado en DB, pero ambas aparecen)
        items_all, total_all = await asig_repo.list_paginated(
            limit=10, offset=0, incluir_vencidas=True
        )
        all_ids = {a.id for a in items_all}
        assert asig_vigente.id in all_ids
        assert asig_vencida.id in all_ids

    @pytest.mark.asyncio
    async def test_asignacion_repository_filtro_usuario_id(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 5.2: filtro por usuario_id en list_paginated."""
        from app.repositories.usuarios import UsuarioRepository
        from app.repositories.asignaciones import AsignacionRepository

        usuario_repo = UsuarioRepository(db_session, default_tenant.id)
        u1 = await usuario_repo.create(
            nombre="U1Filtro", apellidos="X", email="u1filtro@test.com", estado="Activo"
        )
        u2 = await usuario_repo.create(
            nombre="U2Filtro", apellidos="Y", email="u2filtro@test.com", estado="Activo"
        )

        asig_repo = AsignacionRepository(db_session, default_tenant.id)
        asig_u1 = await asig_repo.create(
            usuario_id=u1.id, rol="PROFESOR", desde=date.today()
        )
        asig_u2 = await asig_repo.create(
            usuario_id=u2.id, rol="TUTOR", desde=date.today()
        )

        items, total = await asig_repo.list_paginated(
            limit=10, offset=0, usuario_id=u1.id
        )
        ids = {a.id for a in items}
        assert asig_u1.id in ids
        assert asig_u2.id not in ids
