## Context

C-06 introduce el catálogo académico base del sistema: Carrera, Cohorte y Materia. Estos tres modelos son las anclas de dominio de las que cuelgan prácticamente todos los módulos posteriores. La plataforma ya cuenta con autenticación JWT, multi-tenancy row-level (C-01–C-02) y RBAC (C-04). Este change agrega la capa de dominio académico sin tocar auth ni RBAC core.

**ADR-006 (cerrada)**: `Materia` es la definición única en el catálogo del tenant; `Dictado` (carrera × cohorte de una materia) llega después. C-06 NO incluye `Dictado`.

**PA-07 (resuelta)**: `Cohorte` pertenece a una `Carrera` — unicidad `(tenant_id, carrera_id, nombre)` lo confirma.

**Estado actual**: no existen tablas de Carrera, Cohorte ni Materia en el schema. No hay endpoints ni lógica de negocio para estructura académica.

## Goals / Non-Goals

**Goals:**
- Crear los modelos ORM `Carrera`, `Cohorte`, `Materia` con aislamiento row-level por tenant.
- Implementar repositorios con scope de tenant obligatorio para los tres recursos.
- Implementar servicios con reglas de negocio: unicidad, carrera inactiva, ciclo de vida.
- Exponer endpoints REST ABM para los tres recursos bajo `/api/v1/admin/`, protegidos con `require_permission("estructura:gestionar")`.
- Registrar `estructura:gestionar` en la matriz RBAC asignado al rol ADMIN.
- Cubrir con tests de integración: CRUD completo, unicidad por tenant, aislamiento multi-tenant, transiciones de estado.

**Non-Goals:**
- Modelo `Dictado` (carrera × cohorte de una materia) — es C-07 o posterior.
- Asignaciones docentes — C-07.
- Frontend para gestión de estructura académica — alcance separado.
- Bulk import de carreras/materias desde archivo externo.
- Endpoint público (no-admin) de consulta — los módulos dependientes acceden directamente a los repositorios desde sus servicios.

## Decisions

### D-01: Un solo archivo por capa, no un archivo por entidad

**Decisión**: `models/estructura.py`, `repositories/estructura.py`, `services/estructura.py`, `schemas/estructura.py`, `routers/estructura.py` — un archivo por capa que agrupa las tres entidades del change.

**Alternativa descartada**: un set completo de archivos por entidad (`models/carrera.py`, `models/cohorte.py`, `models/materia.py`, etc.).

**Rationale**: las tres entidades son cohesivas (mismo dominio, mismo permiso de acceso, mismo ciclo de vida). Un archivo por capa mantiene el límite de 500 LOC manejable y evita fragmentación innecesaria. Si en el futuro cada entidad crece en complejidad, se refactoriza a archivos separados sin romper contratos.

---

### D-02: Soft delete con campo `deleted_at` (timestamp nullable)

**Decisión**: las tres entidades usan `deleted_at: DateTime | None` para soft delete. Los repositorios filtran `deleted_at IS NULL` por defecto. El campo `estado` (Activa/Inactiva) es un atributo de ciclo de vida de negocio, independiente del soft delete.

**Rationale**: el proyecto exige auditoría append-only (regla dura). `deleted_at` hace el soft delete explícito y consultable. `estado` modela la lógica de negocio (una carrera inactiva puede reactivarse; una borrada no debería aparecer nunca).

---

### D-03: Unicidad enforced en DB + en Service, no solo en DB

**Decisión**: los índices `UNIQUE` en la DB garantizan la restricción a nivel físico. El `Service` verifica previamente (query de existencia antes de insert/update) y lanza `HTTPException 409` con mensaje legible antes de que la DB dispare un error de constraint.

**Alternativa descartada**: depender exclusivamente del manejo de `IntegrityError` de la DB.

**Rationale**: el manejo de excepciones de DB es frágil y genera mensajes crípticos. La verificación en el Service produce errores semánticos (`"El código TUPAD ya existe en este tenant"`) y permite tests más explícitos. El índice DB es el safety net, no la primera línea de defensa.

---

### D-04: Regla de negocio "carrera inactiva no admite cohortes abiertas" en CohorteService

**Decisión**: `CohorteService` valida que la carrera referenciada esté en estado `Activa` antes de crear una cohorte. Además, al desactivar una carrera, el service verifica que no existan cohortes en estado `Activa` asociadas; si existen, rechaza la desactivación con `HTTPException 409`.

**Alternativa descartada**: manejar esta restricción solo con triggers de DB.

**Rationale**: la lógica de negocio vive en la capa Service (regla dura del proyecto). Los triggers de DB son opacos para tests y dificultan la trazabilidad.

---

### D-05: Estructura de directorios y rutas de endpoints

```
# Backend
app/
├── models/estructura.py         # ORM: Carrera, Cohorte, Materia
├── schemas/estructura.py        # Pydantic: Create/Update/Read DTOs para los tres
├── repositories/estructura.py   # Repos: CarreraRepo, CohorteRepo, MateriaRepo
├── services/estructura.py       # Services: CarreraService, CohorteService, MateriaService
└── api/v1/routers/estructura.py # Router: /admin/carreras, /admin/cohortes, /admin/materias

# Alembic
alembic/versions/004_carrera_cohorte_materia.py

# Tests
tests/
├── test_carrera.py
├── test_cohorte.py
└── test_materia.py
```

**Rutas REST**:
```
POST   /api/v1/admin/carreras              → crear carrera
GET    /api/v1/admin/carreras              → listar (paginado, filtrable por estado)
GET    /api/v1/admin/carreras/{id}         → detalle
PUT    /api/v1/admin/carreras/{id}         → editar
DELETE /api/v1/admin/carreras/{id}         → soft delete

POST   /api/v1/admin/cohortes              → crear cohorte
GET    /api/v1/admin/cohortes              → listar (filtrable por carrera_id, estado)
GET    /api/v1/admin/cohortes/{id}         → detalle
PUT    /api/v1/admin/cohortes/{id}         → editar
DELETE /api/v1/admin/cohortes/{id}         → soft delete

POST   /api/v1/admin/materias              → crear materia
GET    /api/v1/admin/materias              → listar (filtrable por estado)
GET    /api/v1/admin/materias/{id}         → detalle
PUT    /api/v1/admin/materias/{id}         → editar
DELETE /api/v1/admin/materias/{id}         → soft delete
```

Todos los endpoints usan la dependency `require_permission("estructura:gestionar")` (solo ADMIN).

---

### D-06: Campos de auditoría en modelos (created_at, updated_at)

**Decisión**: los tres modelos llevan `created_at`, `updated_at` (auto-gestionados por SQLAlchemy) y `deleted_at`. No llevan `created_by` ni `updated_by` en este change — ese tracking se cubre por el audit log (E-AUD) que se activa en C-05.

**Rationale**: C-05 (audit log) es paralelo a C-06 en el roadmap. En lugar de duplicar lógica de autoría en cada modelo, el audit log provee la traza centralizada. Los campos `created_at`/`updated_at` son suficientes para ordenamiento y debugging.

---

### D-07: Paginación y filtros en listados

**Decisión**: todos los endpoints de listado soportan paginación (`limit`/`offset`) y filtro por `estado`. El endpoint de cohortes también admite filtro por `carrera_id`. El tamaño de página por defecto es 50; máximo 200.

**Rationale**: los catálogos pueden crecer (decenas de carreras, cientos de materias en tenants grandes). Paginación desde el día 0 evita regresiones de rendimiento.

---

### D-08: Relación Carrera → Cohorte en el ORM

**Decisión**: `Cohorte` tiene FK a `Carrera` (`carrera_id`). El ORM SQLAlchemy define la relación `relationship("Cohorte", back_populates="carrera")` pero **lazy loading desactivado** (`lazy="raise"`). Los joins se hacen explícitos en las queries del repository cuando son necesarios.

**Rationale**: lazy loading en FastAPI async es una fuente frecuente de `MissingGreenlet` errors y N+1 queries silenciosas. `lazy="raise"` fuerza al repository a ser explícito.

## Risks / Trade-offs

- **[Riesgo] Migración 004 en conflicto con otras migraciones paralelas** → Dado que C-05 corre en paralelo, si ambas migraciones se ejecutan en ramas que luego se integran, puede haber conflicto de `down_revision`. Mitigación: acordar que las migraciones se numeran y se integran en el orden del roadmap (C-05 antes, C-06 después, o con `alembic merge heads` si fuera necesario).

- **[Trade-off] Unicidad enforced dos veces (Service + DB)** → Doble escritura de lógica de unicidad. El costo es bajo (una query extra de existencia) y el beneficio es claridad semántica en los errores y testabilidad.

- **[Riesgo] Estado de cohortes no se propaga automáticamente al desactivar carrera** → Si se desactiva una carrera, las cohortes activas bajo ella quedan con `estado=Activa` pero bloqueadas para crear nuevas. Mitigación: la regla de negocio rechaza la desactivación de carrera si tiene cohortes activas (D-04). El ADMIN debe desactivar las cohortes primero.

- **[Trade-off] Sin endpoint de bulk import** → No está en scope de C-06. Si un tenant necesita cargar 50 carreras al bootstrap, debe hacerlo una a una vía API o directamente con SQL seed. Se puede agregar en un change futuro sin romper contratos.

## Migration Plan

1. Aplicar migración `004_carrera_cohorte_materia` en entorno de dev/test.
2. Validar con `alembic heads` que no haya ramas abiertas.
3. Ejecutar suite completa de tests: `pytest tests/test_carrera.py tests/test_cohorte.py tests/test_materia.py`.
4. En staging/prod: `alembic upgrade head` — no hay datos pre-existentes que migrar (tablas nuevas).
5. Rollback: `alembic downgrade -1` — `004` solo crea tablas, el downgrade las elimina sin pérdida de datos (tablas vacías en un deploy inicial).

## Open Questions

*(ninguna bloqueante — todas las preguntas abiertas relevantes del dominio están cerradas: ADR-006, PA-07)*
