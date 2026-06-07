## ADDED Requirements

### Requirement: Resolver permisos efectivos desde roles del JWT
El sistema SHALL, dado un `CurrentUser` con `roles` (lista de strings) y `tenant_id`, resolver su conjunto de permisos efectivos como la unión de todos los permisos asignados a esos roles en la matriz `rol_permiso`, filtrando por `tenant_id` y excluyendo registros soft-deleted.

#### Scenario: Usuario con un solo rol tiene permisos de ese rol
- **WHEN** un usuario autenticado tiene el rol `PROFESOR`
- **THEN** su conjunto de permisos efectivos incluye todos los permisos asignados al rol `PROFESOR` en su tenant

#### Scenario: Usuario con múltiples roles tiene unión de permisos
- **WHEN** un usuario autenticado tiene los roles `TUTOR` y `PROFESOR`
- **THEN** su conjunto de permisos efectivos es la unión de los permisos de ambos roles

#### Scenario: Permisos de otro tenant no se incluyen
- **WHEN** un usuario autenticado pertenece al tenant A
- **THEN** ningún permiso asignado a roles del tenant B aparece en sus permisos efectivos

### Requirement: Soportar modificador propio en permisos
El sistema SHALL modelar el modificador `(propio)` como el campo booleano `es_propio` en `rol_permiso`. Cuando `es_propio` es true, el permiso otorgado está restringido a los datos propios del usuario.

#### Scenario: Permiso global vs propio
- **WHEN** el rol `COORDINADOR` tiene `comunicacion:enviar` con `es_propio = false`
- **THEN** un usuario con rol `COORDINADOR` puede enviar comunicaciones sin restricción de propiedad

#### Scenario: Permiso propio restringe a datos del usuario
- **WHEN** el rol `PROFESOR` tiene `calificaciones:importar` con `es_propio = true`
- **THEN** un usuario con rol `PROFESOR` solo puede importar calificaciones de sus propias comisiones

### Requirement: CRUD de catálogo de roles
El sistema SHALL permitir crear, leer, actualizar y soft-deletear roles dentro de un tenant. Cada rol tiene `codigo` (único por tenant), `nombre` y `descripcion`.

#### Scenario: Crear un rol nuevo
- **WHEN** un usuario con permiso `roles:gestionar` crea un rol con código `AUXILIAR`
- **THEN** el rol se persiste en la tabla `rol` con `tenant_id` correspondiente

#### Scenario: Listar roles del tenant
- **WHEN** un usuario autenticado solicita la lista de roles
- **THEN** solo se devuelven roles cuyo `tenant_id` coincide con el del usuario y que no están soft-deleted

#### Scenario: Eliminar un rol (soft delete)
- **WHEN** un usuario con permiso `roles:gestionar` elimina un rol
- **THEN** el campo `deleted_at` del rol se actualiza y sus asignaciones `rol_permiso` quedan inactivas

### Requirement: CRUD de catálogo de permisos
El sistema SHALL permitir crear, leer, actualizar y soft-deletear permisos dentro de un tenant. Cada permiso tiene `codigo` (único por tenant), `nombre`, `descripcion` y `modulo`.

#### Scenario: Crear un permiso nuevo
- **WHEN** un usuario con permiso `permisos:gestionar` crea un permiso con código `reportes:exportar`
- **THEN** el permiso se persiste en la tabla `permiso` con `tenant_id` correspondiente

#### Scenario: Listar permisos del tenant
- **WHEN** un usuario autenticado solicita la lista de permisos
- **THEN** solo se devuelven permisos cuyo `tenant_id` coincide con el del usuario y que no están soft-deleted

### Requirement: CRUD de asignaciones rol-permiso
El sistema SHALL permitir asignar y desasignar permisos a roles mediante la tabla `rol_permiso`, incluyendo el flag `es_propio`.

#### Scenario: Asignar permiso a rol
- **WHEN** un usuario con permiso `roles:gestionar` asigna `comunicacion:enviar` al rol `COORDINADOR` con `es_propio = false`
- **THEN** se crea el registro en `rol_permiso` y los usuarios con ese rol adquieren el permiso

#### Scenario: Quitar permiso a rol (soft delete)
- **WHEN** un usuario con permiso `roles:gestionar` quita un permiso de un rol
- **THEN** el registro en `rol_permiso` se marca como soft-deleted

## MODIFIED Requirements

### Requirement: Auth token claims
El sistema SHALL continuar incluyendo `roles` (lista de strings) en el JWT access token. No se agregan permisos al token.

#### Scenario: Token contiene solo roles
- **WHEN** el sistema genera un access token
- **THEN** el claim `roles` contiene los códigos de rol del usuario y no incluye claim de permisos

## REMOVED Requirements

(Ninguno)
