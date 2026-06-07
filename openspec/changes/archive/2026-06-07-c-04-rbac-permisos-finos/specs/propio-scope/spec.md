## ADDED Requirements

### Requirement: Modificador propio restringe acceso a datos del usuario
El sistema SHALL, cuando un permiso tiene el modificador `(propio)` (`es_propio = true` en `rol_permiso`), restringir la operación a los datos donde el usuario autenticado es el propietario o está directamente asociado.

#### Scenario: Usuario con permiso propio solo ve sus datos
- **WHEN** un usuario con `calificaciones:ver` (propio) solicita calificaciones
- **THEN** el sistema solo devuelve calificaciones de comisiones donde el usuario es docente asignado

#### Scenario: Usuario con permiso global ve todos los datos
- **WHEN** un usuario con `calificaciones:ver` (global, `es_propio = false`) solicita calificaciones
- **THEN** el sistema devuelve calificaciones sin restricción de propiedad

### Requirement: El guard no aplica filtro de propiedad, solo lo marca
El sistema SHALL hacer que `require_permission` devuelva si el permiso es propio, pero NO aplique el filtro de datos propios. El filtro concreto es responsabilidad del service/repository del dominio afectado.

#### Scenario: Service aplica filtro de propiedad
- **WHEN** `require_permission("calificaciones:importar")` devuelve `is_propio = true`
- **THEN** el service de calificaciones agrega `WHERE profesor_id = current_user.id` a la query

### Requirement: Documentar patrón de aplicación de filtro propio
El sistema SHALL documentar en `docs/ARQUITECTURA.md` que todo service que reciba `PermissionContext` con `is_propio = true` debe aplicar el filtro de propiedad correspondiente al dominio.

#### Scenario: Desarrollador implementa endpoint con permiso propio
- **WHEN** un desarrollador agrega un endpoint que usa `require_permission` con un permiso que puede ser propio
- **THEN** el desarrollador consulta la documentación y aplica el filtro de propiedad en el service
