## Why

El sistema necesita un catálogo académico estructurado (Carrera, Cohorte, Materia) para que todos los módulos posteriores — asignaciones docentes, padrón, calificaciones, encuentros, coloquios y liquidaciones — puedan referenciar entidades canónicas con unicidad garantizada por tenant. Sin este catálogo, cada módulo dependiente estaría construyendo sobre arena: IDs ambiguos, datos duplicados y ausencia de aislamiento multi-tenant en la capa de dominio académico.

## What Changes

- **New**: modelos ORM `Carrera`, `Cohorte` y `Materia` con `tenant_id` en cada tabla y soft delete.
- **New**: migración Alembic `004_carrera_cohorte_materia` que crea las tres tablas con los índices de unicidad correspondientes.
- **New**: repositorios `CarreraRepository`, `CohorteRepository`, `MateriaRepository` con scope de tenant obligatorio.
- **New**: servicios `CarreraService`, `CohorteService`, `MateriaService` que encapsulan reglas de negocio (unicidad, carrera inactiva, soft delete).
- **New**: endpoints ABM REST bajo `/api/v1/admin/` para los tres recursos, protegidos con `require_permission("estructura:gestionar")`.
- **New**: schemas Pydantic de request/response con `extra='forbid'` para los tres recursos.
- **New**: permisos `estructura:gestionar` registrado en la matriz RBAC (asignado al rol ADMIN).
- **New**: suite de tests de integración que cubre CRUD, unicidad por tenant, aislamiento multi-tenant y transiciones de estado.

## Capabilities

### New Capabilities

- `carrera-management`: ABM de carreras por tenant — alta, edición, cambio de estado (activa/inactiva), lista paginada. Unicidad `(tenant_id, codigo)`. Una carrera inactiva no puede tener cohortes abiertas.
- `cohorte-management`: ABM de cohortes por tenant — alta, edición, cambio de estado, lista paginada. Cohorte pertenece a una carrera; unicidad `(tenant_id, carrera_id, nombre)`. Crear cohorte activa en carrera inactiva está prohibido.
- `materia-management`: ABM de materias por tenant — alta, edición, cambio de estado (activa/inactiva), lista paginada. Unicidad `(tenant_id, codigo)`. El catálogo es único por tenant (ADR-006).

### Modified Capabilities

*(ninguna — este change introduce capacidades nuevas; no modifica specs existentes)*

## Impact

- **Backend**: creación de `app/models/estructura.py`, `app/repositories/estructura.py`, `app/services/estructura.py`, `app/schemas/estructura.py`, `app/api/v1/routers/estructura.py`; migración Alembic `004_carrera_cohorte_materia`.
- **RBAC seed**: el permiso `estructura:gestionar` se agrega al catálogo de permisos y se asigna al rol ADMIN en el seed/fixture de la matriz.
- **Tests**: `tests/test_carrera.py`, `tests/test_cohorte.py`, `tests/test_materia.py` — todos con DB de test real (sin mocks de BD per regla dura del proyecto).
- **Dependencias**: requiere C-04 (RBAC) completado — los guards `require_permission` y la matriz rol × permiso deben existir antes de poder declararlos en los routers de este change.
- **Dependientes**: C-07 (asignaciones docentes), C-08 (padrón/alumnos), C-09, C-10, C-11, C-12 y todos los módulos que referencian `carrera_id`, `cohorte_id` o `materia_id`.
- **Governance**: MEDIO — lógica de dominio estándar sin tocar auth, RBAC core ni liquidaciones.
