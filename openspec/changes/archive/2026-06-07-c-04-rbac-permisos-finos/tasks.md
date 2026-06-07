## 1. Base de datos — Migración y seed

- [x] 1.1 Crear migración Alembic `002_create_rbac_tables.py`: tablas `rol`, `permiso`, `rol_permiso` con `tenant_id`, soft delete (`deleted_at`), índices `(tenant_id, codigo)`.
- [x] 1.2 Implementar seed de roles del dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS) vinculado al primer tenant existente.
- [x] 1.3 Implementar seed de permisos base derivados de `03_actores_y_roles.md` §3.3.
- [x] 1.4 Implementar seed de matriz `rol_permiso` base, incluyendo `es_propio` según la matriz de negocio.
- [x] 1.5 Ejecutar migración en entorno local y verificar que las tablas y datos se crean correctamente.

## 2. Models y Repositories

- [x] 2.1 Crear model SQLAlchemy `Rol` con columnas: `id` (UUID PK), `tenant_id` (UUID FK), `codigo`, `nombre`, `descripcion`, `created_at`, `deleted_at`.
- [x] 2.2 Crear model SQLAlchemy `Permiso` con columnas: `id` (UUID PK), `tenant_id` (UUID FK), `codigo`, `nombre`, `descripcion`, `modulo`, `created_at`, `deleted_at`.
- [x] 2.3 Crear model SQLAlchemy `RolPermiso` con columnas: `id` (UUID PK), `rol_id` (UUID FK), `permiso_id` (UUID FK), `es_propio` (bool, default false), `created_at`, `deleted_at`.
- [x] 2.4 Crear `RolRepository` con métodos: `get_by_id`, `get_by_codigo`, `list_by_tenant`, `create`, `update`, `soft_delete` — todo filtrado por `tenant_id`.
- [x] 2.5 Crear `PermisoRepository` con métodos: `get_by_id`, `get_by_codigo`, `list_by_tenant`, `create`, `update`, `soft_delete` — todo filtrado por `tenant_id`.
- [x] 2.6 Crear `RolPermisoRepository` con métodos: `list_by_rol`, `list_by_permiso`, `create`, `soft_delete`, `get_permissions_for_roles` (devuelve lista de `(codigo, es_propio)` filtrado por tenant + roles + no soft-deleted).

## 3. Servicios de dominio

- [x] 3.1 Crear `PermissionService` con método `resolve_effective_permissions(tenant_id, role_codes) -> set[tuple[str, bool]]` que use `RolPermisoRepository.get_permissions_for_roles`.
- [x] 3.2 Crear `RolService` con CRUD completo, validando `tenant_id` en cada operación y aplicando soft delete.
- [x] 3.3 Crear `PermisoService` con CRUD completo, validando `tenant_id` en cada operación y aplicando soft delete.
- [x] 3.4 Crear `RolPermisoService` con asignar/quitar permisos a roles, validando que ambos existan en el mismo tenant.

## 4. Schemas Pydantic

- [x] 4.1 Crear `RolCreateSchema`, `RolUpdateSchema`, `RolResponseSchema` con `extra='forbid'`.
- [x] 4.2 Crear `PermisoCreateSchema`, `PermisoUpdateSchema`, `PermisoResponseSchema` con `extra='forbid'`.
- [x] 4.3 Crear `RolPermisoCreateSchema`, `RolPermisoResponseSchema` con `extra='forbid'`.
- [x] 4.4 Crear `PermissionContext` schema (o dataclass) con `has_permission: bool`, `is_propio: bool`, `effective_permissions: set[str]`.

## 5. Guard require_permission

- [x] 5.1 Reemplazar el placeholder `require_permission` en `core/dependencies.py` con la implementación real.
- [x] 5.2 La dependency debe: resolver `CurrentUser` desde JWT, consultar `PermissionService.resolve_effective_permissions`, verificar si el permiso solicitado está en el set, devolver `PermissionContext`.
- [x] 5.3 Si no tiene permiso → lanzar `HTTPException(status_code=403, detail="Permiso denegado")`.
- [x] 5.4 Agregar tests de integración: usuario sin permiso → 403, usuario con permiso → 200, cambio en matriz se refleja sin re-login.

## 6. Routers y endpoints

- [x] 6.1 Crear `RolRouter` (`/api/v1/roles`) con GET, POST, PUT, DELETE, protegido por `require_permission("roles:gestionar")`.
- [x] 6.2 Crear `PermisoRouter` (`/api/v1/permisos`) con GET, POST, PUT, DELETE, protegido por `require_permission("permisos:gestionar")`.
- [x] 6.3 Crear `RolPermisoRouter` (`/api/v1/rol-permisos`) con GET, POST, DELETE, protegido por `require_permission("roles:gestionar")`.
- [x] 6.4 Registrar los tres routers en `main.py`.
- [x] 6.5 Documentar en OpenAPI/FastAPI las respuestas de error (403, 404, 422).

## 7. Tests

- [x] 7.1 Test de integración: usuario con un solo rol tiene exactamente los permisos de esa matriz.
- [x] 7.2 Test de integración: usuario con múltiples roles tiene unión de permisos.
- [x] 7.3 Test de integración: permisos de otro tenant no se incluyen en la resolución.
- [x] 7.4 Test de integración: `require_permission` devuelve `is_propio = true` cuando corresponde.
- [x] 7.5 Test de integración: CRUD completo de roles con DB real (crear, listar, actualizar, soft delete).
- [x] 7.6 Test de integración: CRUD completo de permisos con DB real.
- [x] 7.7 Test de integración: asignar y quitar permisos a roles con DB real.
- [x] 7.8 Cobertura ≥90% de reglas de negocio (resolución de permisos, guard fail-closed, propio).

## 8. Documentación

- [x] 8.1 Actualizar `docs/ARQUITECTURA.md` §5.2 para reflejar que la matriz es catálogo en BD, no hardcode.
- [x] 8.2 Documentar en `docs/ARQUITECTURA.md` el patrón de aplicación de filtro `(propio)` en services/repositories.
- [x] 8.3 Agregar nota en `knowledge-base/10_preguntas_abiertas.md` indicando que ADR-008 (semántica de NEXO) queda marcada como "rol creado sin permisos base, a definir".
