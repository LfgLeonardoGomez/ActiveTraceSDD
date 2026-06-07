## ADDED Requirements

### Requirement: CRUD administrable de roles por tenant
El sistema SHALL exponer endpoints REST para crear, listar, actualizar y eliminar (soft delete) roles dentro del tenant del usuario autenticado.

#### Scenario: Crear rol
- **WHEN** se envía `POST /api/v1/roles` con `{ "codigo": "SUPERVISOR", "nombre": "Supervisor", "descripcion": "..." }`
- **THEN** se crea el rol en la base de datos con `tenant_id` del usuario

#### Scenario: Listar roles
- **WHEN** se envía `GET /api/v1/roles`
- **THEN** se devuelven todos los roles del tenant del usuario que no estén soft-deleted

#### Scenario: Actualizar rol
- **WHEN** se envía `PUT /api/v1/roles/{id}` con datos válidos
- **THEN** se actualiza el rol correspondiente

#### Scenario: Eliminar rol
- **WHEN** se envía `DELETE /api/v1/roles/{id}`
- **THEN** se actualiza `deleted_at` del rol y se marcan como eliminados sus registros en `rol_permiso`

### Requirement: CRUD administrable de permisos por tenant
El sistema SHALL exponer endpoints REST para crear, listar, actualizar y eliminar (soft delete) permisos dentro del tenant del usuario autenticado.

#### Scenario: Crear permiso
- **WHEN** se envía `POST /api/v1/permisos` con `{ "codigo": "reportes:exportar", "nombre": "Exportar reportes", "modulo": "reportes" }`
- **THEN** se crea el permiso en la base de datos con `tenant_id` del usuario

#### Scenario: Listar permisos
- **WHEN** se envía `GET /api/v1/permisos`
- **THEN** se devuelven todos los permisos del tenant del usuario que no estén soft-deleted

### Requirement: CRUD administrable de asignaciones rol-permiso
El sistema SHALL exponer endpoints REST para asignar permisos a roles y quitar asignaciones, incluyendo el flag `es_propio`.

#### Scenario: Asignar permiso a rol
- **WHEN** se envía `POST /api/v1/rol-permisos` con `{ "rol_id": "...", "permiso_id": "...", "es_propio": true }`
- **THEN** se crea la asignación en `rol_permiso`

#### Scenario: Listar permisos de un rol
- **WHEN** se envía `GET /api/v1/roles/{rol_id}/permisos`
- **THEN** se devuelven todos los permisos asignados a ese rol que no estén soft-deleted

#### Scenario: Quitar permiso de rol
- **WHEN** se envía `DELETE /api/v1/rol-permisos/{id}`
- **THEN** se marca como soft-deleted el registro en `rol_permiso`
