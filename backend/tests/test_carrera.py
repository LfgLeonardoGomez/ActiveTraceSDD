"""Tests TDD para C-06 — Carrera (modelos, schemas, repositorio, servicio, router).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR para cada grupo de tasks.
"""

import pytest
from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import AsyncSession

# ============================================================
# GRUPO 2: Modelos ORM
# ============================================================


class TestEstructuraModels:
    """Task 2.1 RED: verificar importación de modelos desde app.models.estructura."""

    def test_import_carrera(self) -> None:
        """RED 2.1: importar Carrera desde app.models.estructura."""
        from app.models.estructura import Carrera
        assert Carrera is not None

    def test_import_cohorte(self) -> None:
        """RED 2.1: importar Cohorte desde app.models.estructura."""
        from app.models.estructura import Cohorte
        assert Cohorte is not None

    def test_import_materia(self) -> None:
        """RED 2.1: importar Materia desde app.models.estructura."""
        from app.models.estructura import Materia
        assert Materia is not None

    def test_carrera_has_required_fields(self) -> None:
        """Task 2.3 TRIANGULATE: instanciar Carrera y verificar campos."""
        from app.models.estructura import Carrera
        from sqlalchemy import inspect as sa_inspect

        mapper = sa_inspect(Carrera)
        column_names = {c.key for c in mapper.columns}

        assert "id" in column_names
        assert "tenant_id" in column_names
        assert "codigo" in column_names
        assert "nombre" in column_names
        assert "estado" in column_names
        assert "created_at" in column_names
        assert "updated_at" in column_names
        assert "deleted_at" in column_names

    def test_cohorte_has_carrera_fk(self) -> None:
        """Task 2.3 TRIANGULATE: Cohorte tiene FK a carreras."""
        from app.models.estructura import Cohorte
        from sqlalchemy import inspect as sa_inspect

        mapper = sa_inspect(Cohorte)
        column_names = {c.key for c in mapper.columns}

        assert "carrera_id" in column_names
        assert "anio" in column_names
        assert "vig_desde" in column_names
        assert "vig_hasta" in column_names

    def test_cohorte_carrera_relationship_is_raise(self) -> None:
        """Task 2.3 TRIANGULATE: relación carrera en Cohorte tiene lazy=raise."""
        from app.models.estructura import Cohorte
        from sqlalchemy import inspect as sa_inspect

        mapper = sa_inspect(Cohorte)
        rel = mapper.relationships["carrera"]
        assert rel.lazy == "raise"

    def test_materia_has_required_fields(self) -> None:
        """Task 2.3 TRIANGULATE: Materia tiene campos correctos."""
        from app.models.estructura import Materia
        from sqlalchemy import inspect as sa_inspect

        mapper = sa_inspect(Materia)
        column_names = {c.key for c in mapper.columns}

        assert "id" in column_names
        assert "tenant_id" in column_names
        assert "codigo" in column_names
        assert "nombre" in column_names
        assert "estado" in column_names
        assert "deleted_at" in column_names


# ============================================================
# GRUPO 3: Schemas Pydantic
# ============================================================


class TestCarreraSchemas:
    """Task 3.1 RED: schemas de Carrera con extra='forbid'."""

    def test_carrera_create_rejects_extra_fields(self) -> None:
        """RED 3.1: CarreraCreate rechaza campos extra."""
        import pytest
        from pydantic import ValidationError
        from app.schemas.estructura import CarreraCreate

        with pytest.raises(ValidationError):
            CarreraCreate(codigo="TUP", nombre="Tecnicatura", campo_extra="x")

    def test_carrera_create_requires_codigo(self) -> None:
        """RED 3.1: CarreraCreate requiere codigo."""
        import pytest
        from pydantic import ValidationError
        from app.schemas.estructura import CarreraCreate

        with pytest.raises(ValidationError):
            CarreraCreate(nombre="Sin codigo")

    def test_carrera_read_includes_id_and_tenant_id(self) -> None:
        """RED 3.1: CarreraRead incluye id y tenant_id."""
        from app.schemas.estructura import CarreraRead

        tenant = uuid4()
        obj = CarreraRead(
            id=uuid4(),
            tenant_id=tenant,
            codigo="TUP",
            nombre="Tecnicatura",
            estado="Activa",
        )
        assert isinstance(obj.id, UUID)
        assert obj.tenant_id == tenant

    def test_carrera_create_valid(self) -> None:
        """GREEN 3.1: CarreraCreate acepta campos correctos."""
        from app.schemas.estructura import CarreraCreate

        obj = CarreraCreate(codigo="TUP", nombre="Tecnicatura")
        assert obj.codigo == "TUP"

    def test_carrera_update_all_optional(self) -> None:
        """GREEN 3.1: CarreraUpdate todos los campos son opcionales."""
        from app.schemas.estructura import CarreraUpdate

        obj = CarreraUpdate()
        assert obj.codigo is None
        assert obj.nombre is None

    def test_carrera_estado_default(self) -> None:
        """GREEN 3.1: CarreraCreate puede incluir estado."""
        from app.schemas.estructura import CarreraCreate

        obj = CarreraCreate(codigo="TUP", nombre="Tecnicatura", estado="Activa")
        assert obj.estado == "Activa"


class TestCohorteYMateriaSchemas:
    """Task 3.3 TRIANGULATE: schemas de Cohorte y Materia."""

    def test_cohorte_create_requires_carrera_id(self) -> None:
        """TRIANGULATE 3.3: CohorteCreate requiere carrera_id."""
        import pytest
        from pydantic import ValidationError
        from app.schemas.estructura import CohorteCreate
        from datetime import date

        with pytest.raises(ValidationError):
            CohorteCreate(nombre="Cohorte 2024", anio=2024, vig_desde=date.today())

    def test_cohorte_create_valid(self) -> None:
        """TRIANGULATE 3.3: CohorteCreate acepta datos válidos."""
        from app.schemas.estructura import CohorteCreate
        from datetime import date

        obj = CohorteCreate(
            carrera_id=uuid4(),
            nombre="Cohorte 2024",
            anio=2024,
            vig_desde=date.today(),
        )
        assert obj.anio == 2024

    def test_cohorte_vig_hasta_optional(self) -> None:
        """TRIANGULATE 3.3: CohorteCreate acepta vig_hasta=None."""
        from app.schemas.estructura import CohorteCreate
        from datetime import date

        obj = CohorteCreate(
            carrera_id=uuid4(),
            nombre="Cohorte Abierta",
            anio=2024,
            vig_desde=date.today(),
            vig_hasta=None,
        )
        assert obj.vig_hasta is None

    def test_cohorte_rejects_extra_fields(self) -> None:
        """TRIANGULATE 3.3: CohorteCreate rechaza campos extra."""
        import pytest
        from pydantic import ValidationError
        from app.schemas.estructura import CohorteCreate
        from datetime import date

        with pytest.raises(ValidationError):
            CohorteCreate(
                carrera_id=uuid4(),
                nombre="C",
                anio=2024,
                vig_desde=date.today(),
                extra="x",
            )

    def test_materia_create_requires_codigo(self) -> None:
        """TRIANGULATE 3.3: MateriaCreate requiere codigo."""
        import pytest
        from pydantic import ValidationError
        from app.schemas.estructura import MateriaCreate

        with pytest.raises(ValidationError):
            MateriaCreate(nombre="Sin codigo")

    def test_materia_create_valid(self) -> None:
        """TRIANGULATE 3.3: MateriaCreate acepta datos válidos."""
        from app.schemas.estructura import MateriaCreate

        obj = MateriaCreate(codigo="MAT101", nombre="Matemática I")
        assert obj.codigo == "MAT101"

    def test_materia_rejects_extra_fields(self) -> None:
        """TRIANGULATE 3.3: MateriaCreate rechaza campos extra."""
        import pytest
        from pydantic import ValidationError
        from app.schemas.estructura import MateriaCreate

        with pytest.raises(ValidationError):
            MateriaCreate(codigo="MAT", nombre="Mat", extra="x")

    def test_materia_read_includes_uuid_fields(self) -> None:
        """TRIANGULATE 3.3: MateriaRead incluye id y tenant_id."""
        from app.schemas.estructura import MateriaRead

        obj = MateriaRead(
            id=uuid4(),
            tenant_id=uuid4(),
            codigo="MAT101",
            nombre="Matemática I",
            estado="Activa",
        )
        assert isinstance(obj.id, UUID)
        assert isinstance(obj.tenant_id, UUID)

    def test_cohorte_read_includes_carrera_id(self) -> None:
        """TRIANGULATE 3.3: CohorteRead incluye carrera_id."""
        from app.schemas.estructura import CohorteRead
        from datetime import date

        obj = CohorteRead(
            id=uuid4(),
            tenant_id=uuid4(),
            carrera_id=uuid4(),
            nombre="Cohorte 2024",
            anio=2024,
            vig_desde=date.today(),
            vig_hasta=None,
            estado="Activa",
        )
        assert isinstance(obj.carrera_id, UUID)


# ============================================================
# GRUPO 4: Repositorios
# ============================================================


class TestCarreraRepository:
    """Task 4.1 RED, 4.2 GREEN, 4.3 TRIANGULATE para CarreraRepository."""

    def test_import_carrera_repository(self) -> None:
        """RED 4.1: importar CarreraRepository."""
        from app.repositories.estructura import CarreraRepository
        assert CarreraRepository is not None

    def test_carrera_repository_has_create(self) -> None:
        """RED 4.1: CarreraRepository tiene método create."""
        from app.repositories.estructura import CarreraRepository
        assert hasattr(CarreraRepository, "create")

    @pytest.mark.asyncio
    async def test_create_carrera(self, db_session: AsyncSession, default_tenant) -> None:
        """GREEN 4.2: crear carrera y recuperarla."""
        from app.repositories.estructura import CarreraRepository

        repo = CarreraRepository(db_session, default_tenant.id)
        carrera = await repo.create(codigo="TUP", nombre="Tecnicatura en Prog.")
        assert carrera.id is not None
        assert carrera.codigo == "TUP"
        assert carrera.tenant_id == default_tenant.id
        assert carrera.estado == "Activa"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_other_tenant(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 4.3: aislamiento — tenant B no ve recursos del tenant A."""
        from app.repositories.estructura import CarreraRepository

        repo_a = CarreraRepository(db_session, default_tenant.id)
        carrera = await repo_a.create(codigo="AISLADA", nombre="Solo A")

        repo_b = CarreraRepository(db_session, uuid4())
        resultado = await repo_b.get_by_id(carrera.id)
        assert resultado is None

    @pytest.mark.asyncio
    async def test_list_paginated_carrera(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 4.2: list_paginated devuelve carreras del tenant."""
        from app.repositories.estructura import CarreraRepository

        repo = CarreraRepository(db_session, default_tenant.id)
        await repo.create(codigo="C1", nombre="Carrera 1")
        await repo.create(codigo="C2", nombre="Carrera 2")

        items, total = await repo.list_paginated(limit=10, offset=0)
        assert total == 2
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_exists_by_codigo(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 4.2: exists_by_codigo detecta duplicados en el tenant."""
        from app.repositories.estructura import CarreraRepository

        repo = CarreraRepository(db_session, default_tenant.id)
        await repo.create(codigo="DUP", nombre="Duplicada")

        assert await repo.exists_by_codigo("DUP") is True
        assert await repo.exists_by_codigo("NODUPLICA") is False

    @pytest.mark.asyncio
    async def test_soft_delete_carrera(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 4.2: soft_delete marca deleted_at."""
        from app.repositories.estructura import CarreraRepository

        repo = CarreraRepository(db_session, default_tenant.id)
        carrera = await repo.create(codigo="DELC", nombre="A Borrar")
        result = await repo.soft_delete(carrera.id)
        assert result is True

        # No debe aparecer en get_by_id estándar
        encontrado = await repo.get_by_id(carrera.id)
        assert encontrado is None


class TestCohorteRepository:
    """Task 4.4 RED, 4.5 TRIANGULATE para CohorteRepository."""

    def test_import_cohorte_repository(self) -> None:
        """RED 4.4: importar CohorteRepository."""
        from app.repositories.estructura import CohorteRepository
        assert CohorteRepository is not None

    @pytest.mark.asyncio
    async def test_create_cohorte(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 4.4: crear cohorte con carrera."""
        from datetime import date
        from app.repositories.estructura import CarreraRepository, CohorteRepository

        carrera_repo = CarreraRepository(db_session, default_tenant.id)
        carrera = await carrera_repo.create(codigo="ING", nombre="Ingeniería")

        cohorte_repo = CohorteRepository(db_session, default_tenant.id)
        cohorte = await cohorte_repo.create(
            carrera_id=carrera.id,
            nombre="2024",
            anio=2024,
            vig_desde=date(2024, 3, 1),
        )
        assert cohorte.id is not None
        assert cohorte.carrera_id == carrera.id
        assert cohorte.estado == "Activa"

    @pytest.mark.asyncio
    async def test_same_nombre_different_carrera_allowed(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 4.5: mismo nombre en diferente carrera es permitido."""
        from datetime import date
        from app.repositories.estructura import CarreraRepository, CohorteRepository

        carrera_repo = CarreraRepository(db_session, default_tenant.id)
        carrera_a = await carrera_repo.create(codigo="CA", nombre="Carrera A")
        carrera_b = await carrera_repo.create(codigo="CB", nombre="Carrera B")

        cohorte_repo = CohorteRepository(db_session, default_tenant.id)
        coh_a = await cohorte_repo.create(
            carrera_id=carrera_a.id, nombre="2024", anio=2024, vig_desde=date(2024, 3, 1)
        )
        coh_b = await cohorte_repo.create(
            carrera_id=carrera_b.id, nombre="2024", anio=2024, vig_desde=date(2024, 3, 1)
        )
        assert coh_a.id != coh_b.id

    @pytest.mark.asyncio
    async def test_count_activas_por_carrera(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 4.4: count_activas_por_carrera retorna cantidad correcta."""
        from datetime import date
        from app.repositories.estructura import CarreraRepository, CohorteRepository

        carrera_repo = CarreraRepository(db_session, default_tenant.id)
        carrera = await carrera_repo.create(codigo="CNT", nombre="Contar")

        cohorte_repo = CohorteRepository(db_session, default_tenant.id)
        await cohorte_repo.create(
            carrera_id=carrera.id, nombre="2023", anio=2023, vig_desde=date(2023, 1, 1)
        )
        await cohorte_repo.create(
            carrera_id=carrera.id, nombre="2024", anio=2024, vig_desde=date(2024, 1, 1)
        )

        count = await cohorte_repo.count_activas_por_carrera(carrera.id)
        assert count == 2


class TestMateriaRepository:
    """Task 4.6 RED, 4.7 TRIANGULATE para MateriaRepository."""

    def test_import_materia_repository(self) -> None:
        """RED 4.6: importar MateriaRepository."""
        from app.repositories.estructura import MateriaRepository
        assert MateriaRepository is not None

    @pytest.mark.asyncio
    async def test_create_materia(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 4.6: crear materia en tenant."""
        from app.repositories.estructura import MateriaRepository

        repo = MateriaRepository(db_session, default_tenant.id)
        materia = await repo.create(codigo="MAT101", nombre="Matemática I")
        assert materia.id is not None
        assert materia.codigo == "MAT101"
        assert materia.tenant_id == default_tenant.id

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation_listado(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 4.7: listado aislado por tenant."""
        from app.repositories.estructura import MateriaRepository

        tenant_b_id = uuid4()
        repo_a = MateriaRepository(db_session, default_tenant.id)
        await repo_a.create(codigo="MAT101", nombre="Matemática I")

        # tenant B no puede ver las materias del tenant A
        repo_b = MateriaRepository(db_session, tenant_b_id)
        items, total = await repo_b.list_paginated(limit=10, offset=0)
        assert total == 0
        assert len(items) == 0


# ============================================================
# GRUPO 5: Servicios
# ============================================================


class TestCarreraService:
    """Task 5.1 RED, 5.2 GREEN, 5.3 TRIANGULATE para CarreraService."""

    def test_import_carrera_service(self) -> None:
        """RED 5.1: importar CarreraService."""
        from app.services.estructura import CarreraService
        assert CarreraService is not None

    @pytest.mark.asyncio
    async def test_crear_carrera_exitosa(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 5.2: crear carrera sin conflicto."""
        from app.services.estructura import CarreraService

        service = CarreraService(db_session, default_tenant.id)
        carrera = await service.crear_carrera(codigo="INGSIS", nombre="Ingeniería en Sistemas")
        assert carrera.codigo == "INGSIS"
        assert carrera.estado == "Activa"

    @pytest.mark.asyncio
    async def test_crear_carrera_codigo_duplicado_409(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 5.2: código duplicado en mismo tenant → 409."""
        from fastapi import HTTPException
        from app.services.estructura import CarreraService

        service = CarreraService(db_session, default_tenant.id)
        await service.crear_carrera(codigo="DUP", nombre="Duplicada")

        with pytest.raises(HTTPException) as exc_info:
            await service.crear_carrera(codigo="DUP", nombre="Duplicada 2")
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_desactivar_carrera_con_cohortes_activas_409(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 5.3: desactivar carrera con cohortes activas → 409."""
        from datetime import date
        from fastapi import HTTPException
        from app.services.estructura import CarreraService, CohorteService

        carrera_svc = CarreraService(db_session, default_tenant.id)
        carrera = await carrera_svc.crear_carrera(codigo="CON_COH", nombre="Con Cohortes")

        cohorte_svc = CohorteService(db_session, default_tenant.id)
        await cohorte_svc.crear_cohorte(
            carrera_id=carrera.id,
            nombre="2024",
            anio=2024,
            vig_desde=date(2024, 3, 1),
        )

        with pytest.raises(HTTPException) as exc_info:
            await carrera_svc.desactivar_carrera(carrera.id)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_desactivar_carrera_sin_cohortes_activas_ok(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 5.3: desactivar carrera sin cohortes activas → OK."""
        from app.services.estructura import CarreraService

        service = CarreraService(db_session, default_tenant.id)
        carrera = await service.crear_carrera(codigo="SINC", nombre="Sin Cohortes")
        resultado = await service.desactivar_carrera(carrera.id)
        assert resultado.estado == "Inactiva"


class TestCohorteService:
    """Task 5.5 RED, 5.6 GREEN, 5.7 TRIANGULATE para CohorteService."""

    @pytest.mark.asyncio
    async def test_crear_cohorte_con_carrera_inactiva_409(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 5.5: crear cohorte con carrera inactiva → 409."""
        from datetime import date
        from fastapi import HTTPException
        from app.services.estructura import CarreraService, CohorteService

        carrera_svc = CarreraService(db_session, default_tenant.id)
        carrera = await carrera_svc.crear_carrera(codigo="INAC", nombre="Inactiva")
        await carrera_svc.desactivar_carrera(carrera.id)

        cohorte_svc = CohorteService(db_session, default_tenant.id)
        with pytest.raises(HTTPException) as exc_info:
            await cohorte_svc.crear_cohorte(
                carrera_id=carrera.id,
                nombre="2024",
                anio=2024,
                vig_desde=date(2024, 3, 1),
            )
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_crear_cohorte_con_carrera_activa_ok(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 5.6: crear cohorte con carrera activa → OK."""
        from datetime import date
        from app.services.estructura import CarreraService, CohorteService

        carrera_svc = CarreraService(db_session, default_tenant.id)
        carrera = await carrera_svc.crear_carrera(codigo="ACT_COH", nombre="Activa")

        cohorte_svc = CohorteService(db_session, default_tenant.id)
        cohorte = await cohorte_svc.crear_cohorte(
            carrera_id=carrera.id,
            nombre="2024",
            anio=2024,
            vig_desde=date(2024, 3, 1),
        )
        assert cohorte.id is not None
        assert cohorte.estado == "Activa"

    @pytest.mark.asyncio
    async def test_reactivar_cohorte_con_carrera_inactiva_409(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 5.7: reactivar cohorte con carrera inactiva → 409."""
        from datetime import date
        from fastapi import HTTPException
        from app.services.estructura import CarreraService, CohorteService

        carrera_svc = CarreraService(db_session, default_tenant.id)
        carrera = await carrera_svc.crear_carrera(codigo="REAC", nombre="Reactivar")

        cohorte_svc = CohorteService(db_session, default_tenant.id)
        cohorte = await cohorte_svc.crear_cohorte(
            carrera_id=carrera.id,
            nombre="2024",
            anio=2024,
            vig_desde=date(2024, 3, 1),
        )

        # Desactivar cohorte, luego desactivar carrera
        await cohorte_svc.cambiar_estado_cohorte(cohorte.id, "Inactiva")
        await carrera_svc.desactivar_carrera(carrera.id)

        # Intentar reactivar la cohorte con carrera inactiva → 409
        with pytest.raises(HTTPException) as exc_info:
            await cohorte_svc.cambiar_estado_cohorte(cohorte.id, "Activa")
        assert exc_info.value.status_code == 409


class TestRepositoryNullPaths:
    """Tests adicionales para cubrir ramas None en repositorios y servicios."""

    @pytest.mark.asyncio
    async def test_carrera_soft_delete_not_found_returns_false(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: soft_delete de carrera no existente retorna False."""
        from app.repositories.estructura import CarreraRepository
        repo = CarreraRepository(db_session, default_tenant.id)
        result = await repo.soft_delete(uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_carrera_update_not_found_returns_none(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: update de carrera no existente retorna None."""
        from app.repositories.estructura import CarreraRepository
        repo = CarreraRepository(db_session, default_tenant.id)
        result = await repo.update(uuid4(), {"nombre": "No existe"})
        assert result is None

    @pytest.mark.asyncio
    async def test_cohorte_list_with_estado_filter(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: list_paginated cohorte con filtro estado."""
        from datetime import date
        from app.repositories.estructura import CarreraRepository, CohorteRepository
        carrera_repo = CarreraRepository(db_session, default_tenant.id)
        carrera = await carrera_repo.create(codigo="CLIST", nombre="List Coh")
        cohorte_repo = CohorteRepository(db_session, default_tenant.id)
        await cohorte_repo.create(
            carrera_id=carrera.id, nombre="2024", anio=2024, vig_desde=date(2024, 3, 1)
        )
        items, total = await cohorte_repo.list_paginated(limit=10, offset=0, estado="Activa")
        assert total >= 1

    @pytest.mark.asyncio
    async def test_cohorte_soft_delete_not_found_returns_false(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: soft_delete de cohorte no existente retorna False."""
        from app.repositories.estructura import CohorteRepository
        repo = CohorteRepository(db_session, default_tenant.id)
        result = await repo.soft_delete(uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_cohorte_update_not_found_returns_none(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: update de cohorte no existente retorna None."""
        from app.repositories.estructura import CohorteRepository
        repo = CohorteRepository(db_session, default_tenant.id)
        result = await repo.update(uuid4(), {"nombre": "No existe"})
        assert result is None

    @pytest.mark.asyncio
    async def test_materia_get_by_id(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: get_by_id de materia existente."""
        from app.repositories.estructura import MateriaRepository
        repo = MateriaRepository(db_session, default_tenant.id)
        materia = await repo.create(codigo="GETM", nombre="Get Materia")
        found = await repo.get_by_id(materia.id)
        assert found is not None
        assert found.id == materia.id

    @pytest.mark.asyncio
    async def test_materia_list_with_estado_filter(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: list_paginated materia con filtro estado."""
        from app.repositories.estructura import MateriaRepository
        repo = MateriaRepository(db_session, default_tenant.id)
        await repo.create(codigo="LMAT", nombre="List Materia")
        items, total = await repo.list_paginated(limit=10, offset=0, estado="Activa")
        assert total >= 1

    @pytest.mark.asyncio
    async def test_materia_update_existing(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: update de materia existente."""
        from app.repositories.estructura import MateriaRepository
        repo = MateriaRepository(db_session, default_tenant.id)
        materia = await repo.create(codigo="UPDM", nombre="Upd Materia")
        updated = await repo.update(materia.id, {"nombre": "Updated Materia"})
        assert updated is not None
        assert updated.nombre == "Updated Materia"

    @pytest.mark.asyncio
    async def test_materia_soft_delete_not_found_returns_false(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: soft_delete de materia no existente retorna False."""
        from app.repositories.estructura import MateriaRepository
        repo = MateriaRepository(db_session, default_tenant.id)
        result = await repo.soft_delete(uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_materia_exists_by_codigo_with_exclude(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: exists_by_codigo con exclude_id."""
        from app.repositories.estructura import MateriaRepository
        repo = MateriaRepository(db_session, default_tenant.id)
        materia = await repo.create(codigo="EXCL", nombre="Exclude")
        # El mismo id excluido no debe contar como duplicado
        exists = await repo.exists_by_codigo("EXCL", exclude_id=materia.id)
        assert exists is False

    @pytest.mark.asyncio
    async def test_obtener_carrera_not_found_404(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: obtener_carrera lanza 404 cuando no existe."""
        from fastapi import HTTPException
        from app.services.estructura import CarreraService
        service = CarreraService(db_session, default_tenant.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.obtener_carrera(uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_obtener_cohorte_not_found_404(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: obtener_cohorte lanza 404 cuando no existe."""
        from fastapi import HTTPException
        from app.services.estructura import CohorteService
        service = CohorteService(db_session, default_tenant.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.obtener_cohorte(uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_obtener_materia_not_found_404(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: obtener_materia lanza 404 cuando no existe."""
        from fastapi import HTTPException
        from app.services.estructura import MateriaService
        service = MateriaService(db_session, default_tenant.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.obtener_materia(uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_actualizar_materia_exitosa(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: actualizar_materia actualiza campos."""
        from app.services.estructura import MateriaService
        service = MateriaService(db_session, default_tenant.id)
        materia = await service.crear_materia(codigo="SVCUPD", nombre="Original")
        actualizada = await service.actualizar_materia(materia.id, {"nombre": "Actualizada"})
        assert actualizada.nombre == "Actualizada"

    @pytest.mark.asyncio
    async def test_eliminar_cohorte_exitosa(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: eliminar_cohorte realiza soft delete."""
        from datetime import date
        from app.services.estructura import CarreraService, CohorteService
        carrera_svc = CarreraService(db_session, default_tenant.id)
        carrera = await carrera_svc.crear_carrera(codigo="ELIM_COH", nombre="Eliminar Coh")
        cohorte_svc = CohorteService(db_session, default_tenant.id)
        cohorte = await cohorte_svc.crear_cohorte(
            carrera_id=carrera.id, nombre="2024", anio=2024, vig_desde=date(2024, 3, 1)
        )
        result = await cohorte_svc.eliminar_cohorte(cohorte.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_eliminar_materia_exitosa(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """Task 8.3 coverage: eliminar_materia realiza soft delete."""
        from app.services.estructura import MateriaService
        service = MateriaService(db_session, default_tenant.id)
        materia = await service.crear_materia(codigo="ELIMMAT", nombre="A Borrar")
        result = await service.eliminar_materia(materia.id)
        assert result is True


class TestMateriaService:
    """Task 5.8 RED, 5.9 GREEN, 5.10 TRIANGULATE para MateriaService."""

    @pytest.mark.asyncio
    async def test_crear_materia_codigo_duplicado_mismo_tenant_409(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """RED 5.8: código duplicado en mismo tenant → 409."""
        from fastapi import HTTPException
        from app.services.estructura import MateriaService

        service = MateriaService(db_session, default_tenant.id)
        await service.crear_materia(codigo="DUPMAT", nombre="Duplicada")

        with pytest.raises(HTTPException) as exc_info:
            await service.crear_materia(codigo="DUPMAT", nombre="Duplicada 2")
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_crear_materia_exitosa(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """GREEN 5.9: crear materia sin conflicto."""
        from app.services.estructura import MateriaService

        service = MateriaService(db_session, default_tenant.id)
        materia = await service.crear_materia(codigo="FIS101", nombre="Física I")
        assert materia.codigo == "FIS101"

    @pytest.mark.asyncio
    async def test_codigo_duplicado_en_otro_tenant_no_conflicto(
        self, db_session: AsyncSession, default_tenant
    ) -> None:
        """TRIANGULATE 5.10: mismo código en otro tenant no produce conflicto."""
        from app.models.tenant import Tenant
        from app.services.estructura import MateriaService

        service_a = MateriaService(db_session, default_tenant.id)
        await service_a.crear_materia(codigo="SHARED", nombre="Compartida A")

        # Crear un segundo tenant real (FK constraint)
        tenant_b = Tenant(nombre="Tenant B", slug="tenant-b-mat", activo=True)
        db_session.add(tenant_b)
        await db_session.commit()
        await db_session.refresh(tenant_b)

        service_b = MateriaService(db_session, tenant_b.id)
        materia_b = await service_b.crear_materia(codigo="SHARED", nombre="Compartida B")
        assert materia_b is not None
        assert materia_b.codigo == "SHARED"
