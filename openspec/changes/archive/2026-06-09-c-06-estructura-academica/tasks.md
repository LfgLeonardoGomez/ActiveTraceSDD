## 1. Migración de base de datos

- [x] 1.1 Crear migración Alembic `004_carrera_cohorte_materia` con tabla `carreras` (columnas: `id UUID PK`, `tenant_id UUID NOT NULL`, `codigo TEXT NOT NULL`, `nombre TEXT NOT NULL`, `estado TEXT NOT NULL DEFAULT 'Activa'`, `created_at`, `updated_at`, `deleted_at`); índice único `(tenant_id, codigo) WHERE deleted_at IS NULL`
- [x] 1.2 Agregar tabla `cohortes` en la misma migración (columnas: `id UUID PK`, `tenant_id UUID NOT NULL`, `carrera_id UUID NOT NULL FK→carreras.id`, `nombre TEXT NOT NULL`, `anio INTEGER NOT NULL`, `vig_desde DATE NOT NULL`, `vig_hasta DATE NULL`, `estado TEXT NOT NULL DEFAULT 'Activa'`, `created_at`, `updated_at`, `deleted_at`); índice único `(tenant_id, carrera_id, nombre) WHERE deleted_at IS NULL`
- [x] 1.3 Agregar tabla `materias` en la misma migración (columnas: `id UUID PK`, `tenant_id UUID NOT NULL`, `codigo TEXT NOT NULL`, `nombre TEXT NOT NULL`, `estado TEXT NOT NULL DEFAULT 'Activa'`, `created_at`, `updated_at`, `deleted_at`); índice único `(tenant_id, codigo) WHERE deleted_at IS NULL`
- [x] 1.4 Verificar que `alembic upgrade head` aplica sin errores y `alembic downgrade -1` revierte limpiamente

## 2. Modelos ORM

- [x] 2.1 Escribir test RED: verificar que importar `Carrera`, `Cohorte`, `Materia` desde `app.models.estructura` falla (módulo no existe)
- [x] 2.2 Crear `app/models/estructura.py` con clases SQLAlchemy `Carrera`, `Cohorte`, `Materia`; cada una con `tenant_id`, `estado`, `created_at`, `updated_at`, `deleted_at`; relación `Cohorte.carrera` con `lazy="raise"`; verificar que el test pasa (GREEN)
- [x] 2.3 Triangular: agregar test que instancia los modelos y verifica que los campos y tipos son correctos; refactorizar si hay duplicación

## 3. Schemas Pydantic

- [x] 3.1 Escribir tests RED para schemas de Carrera: verificar que campos extra son rechazados (`extra='forbid'`), que `codigo` es obligatorio, que la respuesta incluye `id` y `tenant_id`
- [x] 3.2 Crear `app/schemas/estructura.py` con `CarreraCreate`, `CarreraUpdate`, `CarreraRead`; `CohorteCreate`, `CohorteUpdate`, `CohorteRead`; `MateriaCreate`, `MateriaUpdate`, `MateriaRead`; todos con `model_config = ConfigDict(extra='forbid')`; verificar que los tests pasan
- [x] 3.3 Triangular: agregar tests para schemas de Cohorte y Materia (campos obligatorios, campos opcionales, validación de `estado` como enum); refactorizar si hay duplicación

## 4. Repositorios

- [x] 4.1 Escribir test RED para `CarreraRepository.create`: verificar que la función no existe y que el test falla por `ImportError` o `AttributeError`
- [x] 4.2 Crear `app/repositories/estructura.py` con `CarreraRepository` (métodos: `create`, `get_by_id`, `list_paginated`, `update`, `soft_delete`, `exists_by_codigo`); cada método filtra por `tenant_id` y `deleted_at IS NULL` por defecto; verificar que el test GREEN pasa con DB de test real
- [x] 4.3 Triangular para `CarreraRepository`: test de aislamiento — crear carrera en tenant A, verificar que `get_by_id` desde tenant B retorna `None`
- [x] 4.4 Escribir test RED para `CohorteRepository.create` y agregar `CohorteRepository` al mismo archivo (métodos: `create`, `get_by_id`, `list_paginated`, `update`, `soft_delete`, `exists_by_nombre_en_carrera`, `count_activas_por_carrera`); verificar GREEN
- [x] 4.5 Triangular para `CohorteRepository`: test de unicidad por `(tenant_id, carrera_id, nombre)` — crear cohorte con mismo nombre en carrera diferente del mismo tenant debe ser permitido
- [x] 4.6 Escribir test RED para `MateriaRepository.create` y agregar `MateriaRepository` al mismo archivo (métodos: `create`, `get_by_id`, `list_paginated`, `update`, `soft_delete`, `exists_by_codigo`); verificar GREEN
- [x] 4.7 Triangular para `MateriaRepository`: test de aislamiento multi-tenant en listado — dos tenants con misma materia código, listado de cada uno solo muestra sus propias materias

## 5. Servicios

- [x] 5.1 Escribir test RED para `CarreraService.crear_carrera`: verificar que el service no existe
- [x] 5.2 Crear `app/services/estructura.py` con `CarreraService` (métodos: `crear_carrera`, `listar_carreras`, `obtener_carrera`, `actualizar_carrera`, `desactivar_carrera`, `eliminar_carrera`); el service valida unicidad antes de insertar (query al repo), lanza `HTTPException 409` si el código existe en el tenant; verificar GREEN con test real
- [x] 5.3 Triangular para `CarreraService`: test de desactivación con cohortes activas — debe lanzar `HTTPException 409`; test de desactivación sin cohortes activas — debe pasar
- [x] 5.4 Refactorizar `CarreraService` si hay lógica duplicada; re-ejecutar tests (deben quedar verdes)
- [x] 5.5 Escribir test RED para `CohorteService.crear_cohorte` con carrera inactiva — debe fallar con 409
- [x] 5.6 Agregar `CohorteService` al mismo archivo (métodos: `crear_cohorte`, `listar_cohortes`, `obtener_cohorte`, `actualizar_cohorte`, `cambiar_estado_cohorte`, `eliminar_cohorte`); el service valida que la carrera esté activa antes de crear; al reactivar una cohorte, valida que la carrera esté activa; verificar GREEN
- [x] 5.7 Triangular para `CohorteService`: test de reactivación de cohorte con carrera inactiva — debe lanzar `HTTPException 409`
- [x] 5.8 Escribir test RED para `MateriaService.crear_materia` con código duplicado en el tenant
- [x] 5.9 Agregar `MateriaService` al mismo archivo (métodos: `crear_materia`, `listar_materias`, `obtener_materia`, `actualizar_materia`, `cambiar_estado_materia`, `eliminar_materia`); verificar GREEN
- [x] 5.10 Triangular para `MateriaService`: test de código duplicado en otro tenant no produce conflicto

## 6. Endpoints REST (Routers)

- [x] 6.1 Escribir test RED para `POST /api/v1/admin/carreras` — verificar que la ruta no existe (404)
- [x] 6.2 Crear `app/api/v1/routers/estructura.py` con el router de carreras (`POST`, `GET`, `GET/{id}`, `PUT/{id}`, `DELETE/{id}`); cada endpoint declara `require_permission("estructura:gestionar")`; tenant e identidad del actor se obtienen exclusivamente del JWT verificado; registrar el router en `app/main.py` con prefijo `/api/v1/admin`; verificar GREEN para el test de creación
- [x] 6.3 Triangular para router de carreras: test que un usuario sin `estructura:gestionar` recibe 403; test de listado paginado con filtro por estado; test de edición con código duplicado retorna 409
- [x] 6.4 Agregar router de cohortes al mismo archivo (`POST`, `GET`, `GET/{id}`, `PUT/{id}`, `DELETE/{id}`); escribir test RED para `POST /api/v1/admin/cohortes` con carrera inactiva; verificar GREEN
- [x] 6.5 Triangular para router de cohortes: test de filtro por `carrera_id`; test de aislamiento (cohorte de otro tenant retorna 404)
- [x] 6.6 Agregar router de materias al mismo archivo (`POST`, `GET`, `GET/{id}`, `PUT/{id}`, `DELETE/{id}`); escribir test RED para `POST /api/v1/admin/materias` con campo extra (debe retornar 422); verificar GREEN
- [x] 6.7 Triangular para router de materias: test de código duplicado retorna 409; test de soft delete (DELETE retorna 204, GET posterior retorna 404)

## 7. RBAC — Permiso `estructura:gestionar`

- [x] 7.1 Agregar el permiso `estructura:gestionar` al fixture/seed de la matriz RBAC en el rol ADMIN (en el archivo de seed o fixture de BD de tests según la implementación de C-04)
- [x] 7.2 Verificar que los tests de endpoints usan un token JWT con rol ADMIN que incluye el permiso; si el fixture de C-04 ya provee un helper de autenticación de test, usarlo directamente

## 8. Tests de integración transversales

- [x] 8.1 Escribir test de aislamiento cross-tenant completo: crear recursos en tenant A (carrera + cohorte + materia), autenticarse como ADMIN del tenant B, verificar que `GET /api/v1/admin/carreras`, `GET /api/v1/admin/cohortes`, `GET /api/v1/admin/materias` retornan listas vacías (cero recursos del tenant A)
- [x] 8.2 Escribir test del flujo completo de ciclo de vida de carrera: crear → listar → editar → desactivar (con cohorte activa: 409) → desactivar cohorte → desactivar carrera → eliminar carrera
- [x] 8.3 Verificar cobertura: ejecutar `pytest --cov=app/models/estructura.py --cov=app/repositories/estructura.py --cov=app/services/estructura.py --cov=app/api/v1/routers/estructura.py` y confirmar ≥80% líneas, ≥90% en reglas de negocio (unicidad, carrera inactiva, aislamiento)

## 9. Calidad y cierre

- [x] 9.1 Verificar que todos los archivos backend creados tienen ≤500 LOC (`wc -l` o equivalente en Windows)
- [x] 9.2 Verificar que todos los schemas Pydantic tienen `model_config = ConfigDict(extra='forbid')` explícito
- [x] 9.3 Verificar que ningún router accede directamente a la DB (debe ir por Service → Repository)
- [x] 9.4 Ejecutar la suite completa: `pytest tests/test_carrera.py tests/test_cohorte.py tests/test_materia.py -v` — todos deben pasar
- [x] 9.5 Marcar [x] el change `C-06` en `CHANGES.md`
