## Why

C-03 estableció autenticación JWT con roles en el token, pero la autorización sigue siendo un placeholder: `require_permission` devuelve 403 sin verificar permisos reales. activia-trace necesita un modelo RBAC con permisos finos (`modulo:accion`) resueltos server-side en cada petición, donde la matriz rol × permiso sea un catálogo administrable (datos, no hardcode). Este change es la puerta de salida del camino crítico secuencial: tras C-04, se abre el primer fork paralelo (C-05 audit-log, C-06 estructura-académica, C-21 frontend-shell-y-auth).

## What Changes

- **Nuevas tablas de catálogo**: `rol`, `permiso`, `rol_permiso` con `tenant_id` y soft delete. Migración Alembic `002`.
- **Seed de roles del dominio**: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS, cada uno con su matriz de permisos base derivada de `03_actores_y_roles.md` §3.3.
- **Resolución de permisos efectivos**: algoritmo server-side que, dado un `CurrentUser` (con `roles`), consulta `rol_permiso` filtrado por tenant y devuelve el conjunto de permisos efectivos como unión de todos sus roles.
- **Guard `require_permission` real**: reemplaza el placeholder de C-03. Cada endpoint declara `require_permission("modulo:accion")`; sin permiso explícito → `403`. Fail-closed.
- **Modificador `(propio)`**: ciertos permisos (p. ej. `calificaciones:importar` para PROFESOR) son scoped a datos propios del usuario. El guard debe propagar esta marca para que el service/repository aplique el filtro adicional.
- **Tests**: 403 para usuario sin permiso, unión de roles, permiso `(propio)` vs global, catálogo administrable CRUD.

## Capabilities

### New Capabilities
- `rbac-core`: Resolución server-side de permisos efectivos a partir de roles, tenant y matriz rol-permiso.
- `permission-guard`: Dependency `require_permission` para endpoints FastAPI. Fail-closed: sin permiso → 403.
- `role-permission-catalog`: CRUD administrable de roles, permisos y asignaciones `rol_permiso` dentro de un tenant.
- `propio-scope`: Modificador `(propio)` que restringe un permiso a los datos propios del usuario autenticado.

### Modified Capabilities
- `auth` (de C-03): el campo `roles` del `CurrentUser` ahora se consume por el sistema RBAC para resolver permisos efectivos. No cambia la firma del token, solo el uso interno.

## Impact

- **Backend**: nuevos models, repositories, services, schemas Pydantic en módulo RBAC. Modificación de `core/dependencies.py` para reemplazar `require_permission` placeholder. Migración `002`.
- **Base de datos**: tablas `rol`, `permiso`, `rol_permiso` en PostgreSQL.
- **API**: endpoints de catálogo (`GET/POST/PUT/DELETE /api/v1/roles`, `/permisos`, `/rol-permisos`).
- **Dependencias**: requiere C-03 (auth JWT + `CurrentUser` con `roles`). Bloquea C-05, C-06, C-21.
