## Context

C-03 entregó autenticación JWT con `CurrentUser.roles` (lista de strings de roles) y un placeholder `require_permission` que siempre devuelve 403. Ahora se necesita:

1. Persistir la matriz rol × permiso en la base de datos (catálogo administrable por tenant).
2. Resolver permisos efectivos server-side a partir de los roles del JWT + la matriz en BD.
3. Reemplazar el placeholder `require_permission` con lógica real que falle cerrado (sin permiso → 403).
4. Soportar el modificador `(propio)` para permisos scoped a datos del usuario autenticado.

El diseño debe respetar Clean Architecture (Routers → Services → Repositories → Models), multi-tenancy row-level con `tenant_id` en cada query, y soft delete en todas las entidades.

## Goals / Non-Goals

**Goals:**
- Modelo de datos: tablas `rol`, `permiso`, `rol_permiso` con tenant scope y soft delete.
- Seed de la matriz base de 7 roles del dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) según `03_actores_y_roles.md` §3.3.
- Algoritmo de resolución de permisos efectivos: unión de permisos de todos los roles del usuario, filtrado por tenant.
- Dependency `require_permission("modulo:accion")` funcional y fail-closed.
- Modificador `(propio)` propagado desde el guard hasta el service/repository.
- CRUD administrable de roles, permisos y asignaciones `rol_permiso`.
- Tests con DB real: 403 sin permiso, unión de roles, `(propio)`, catálogo CRUD.

**Non-Goals:**
- Vigencia temporal de asignaciones (fechas desde/hasta) — eso viene en un change posterior (C-07 o similar). En C-04 las asignaciones rol-permiso son estáticas por tenant.
- Impersonación — depende de audit-log (C-05) y se define en ADR-004.
- UI frontend para administrar el catálogo — eso viene en C-21 o posterior.

## Decisions

### 1. Tablas: `rol`, `permiso`, `rol_permiso` con `tenant_id`
- Cada tabla lleva `tenant_id` (UUID, NOT NULL, FK a `tenants.id`).
- `rol` y `permiso` tienen `codigo` único por tenant (no global), `nombre`, `descripcion`, `created_at`, `deleted_at`.
- `rol_permiso` es una tabla de unión con `rol_id`, `permiso_id`, `es_propio` (boolean, default false), `created_at`, `deleted_at`.
- Índice compuesto `(tenant_id, codigo)` en `rol` y `permiso` para lookups rápidos.

**Rationale**: el catálogo debe ser administrable por tenant, no hardcodeado. El campo `es_propio` modela el modificador `(propio)` de la matriz de negocio.

### 2. Permisos se resuelven en cada request, no se cachean en el token
- El JWT solo lleva `roles` (lista de strings).
- En cada request, un service consulta `rol_permiso` filtrando por `tenant_id` + `rol.codigo IN roles` + `deleted_at IS NULL`.
- El resultado es un `set` de tuplas `(permiso_codigo, es_propio)`.

**Rationale**: evita stale permissions si el catálogo cambia. El costo es una query extra por request, mitigable con caché en memoria por tenant+roles (TTL 60s) en una fase posterior si es necesario.

### 3. `require_permission` devuelve un objeto de contexto, no solo un bool
- La dependency devuelve un `PermissionContext` con: `has_permission: bool`, `is_propio: bool`, `effective_permissions: set[str]`.
- Si `has_permission` es false → `HTTPException 403`.
- Si `is_propio` es true, el service/repository downstream debe aplicar el filtro de propiedad.

**Rationale**: el guard no puede aplicar el filtro de datos propios porque no conoce el dominio del endpoint (¿es un alumno propio? ¿una comisión propia?). Debe delegar la marca `is_propio` al service.

### 4. Seed de la matriz base como migración de datos (data migration)
- La migración `002` crea las tablas y luego inserta los 7 roles del dominio, los permisos base y la matriz `rol_permiso` según `03_actores_y_roles.md` §3.3.
- El seed usa `tenant_id` de un tenant "sistema" o del primer tenant creado. Dado que C-03 crea el primer tenant, la migración puede hacer un `SELECT id FROM tenants LIMIT 1` para asociar el seed.

**Rationale**: la matriz base debe existir desde el primer deploy. Como es data, va en migración. El seed por tenant se hará en el provisioning de nuevos tenants (post-MVP).

### 5. Sin roles hardcodeados en código
- El único conocimiento hardcodeado es el seed inicial. Después de eso, los roles son data pura.
- El `CurrentUser.roles` sigue siendo una lista de strings (códigos de rol), que se mapean a filas de la tabla `rol`.

**Rationale**: la KB dice "el conjunto de roles debe ser un catálogo administrable por tenant". Respetamos esto desde el diseño.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Query extra por request para resolver permisos → latencia | Aceptado por ahora. Mitigación futura: caché en memoria (TTL 60s) por `(tenant_id, roles)` en `PermissionService`. |
| Seed de matriz base puede desincronizarse con la KB | El seed se documenta explícitamente como derivado de `03_actores_y_roles.md` §3.3. Cualquier cambio en la matriz requiere revisar la migración. |
| Modificador `(propio)` requiere que cada service aplique el filtro correctamente | Documentar el patrón: si `PermissionContext.is_propio` es true, el service debe agregar `WHERE owner_id = current_user.id` (o equivalente). Agregar test de integración que verifique el filtro. |
| Tenant sin seed de roles queda sin permisos | La migración 002 seedea para el primer tenant. El provisioning de nuevos tenants (futuro) debe incluir el seed de roles base. |

## Migration Plan

1. Ejecutar migración Alembic `002_create_rbac_tables.py` (crea tablas + seed).
2. Reemplazar `require_permission` placeholder en `core/dependencies.py`.
3. Agregar módulo RBAC: models, repositories, services, schemas, routers.
4. Correr tests de integración con DB real.
5. No requiere rollback de datos de usuario; las nuevas tablas son catálogo puro.

## Open Questions — Resueltas (2026-06-07)

1. **¿El rol NEXO tiene permisos definidos en la matriz base?** → **Resuelto**: NEXO se crea sin permisos asignados (matriz vacía). La semántica se definirá cuando se cierre PA-25 (pregunta abierta del dominio).
2. **¿Qué tenant recibe el seed inicial?** → **Resuelto**: El seed de la migración 002 se asocia al **primer tenant existente** (`SELECT id FROM tenants WHERE deleted_at IS NULL ORDER BY created_at LIMIT 1`), creado en C-01/C-02. Cada nuevo tenant tendrá su propio seed como parte del provisioning (post-MVP).
3. **¿La matriz base es editable o inmutable?** → **Resuelto**: El seed es **punto de partida editable**. Cada tenant puede modificar su catálogo de roles y permisos después del seed inicial.
