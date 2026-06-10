## ADDED Requirements

### Requirement: Crear asignación de rol en contexto académico
El sistema SHALL crear una asignación que vincule un Usuario con un Rol dentro de un contexto académico (Materia, Carrera, Cohorte, Comisiones). La asignación DEBE incluir rango de vigencia (`desde`, `hasta`). El campo `responsable_id` es opcional y representa al coordinador que supervisa al asignado. Todos los FKs referenciados (usuario_id, materia_id, carrera_id, cohorte_id, responsable_id) deben existir en el mismo tenant.

#### Scenario: Creación exitosa de asignación con contexto completo
- **WHEN** un actor con permiso `equipos:asignar` envía `POST /api/v1/asignaciones` con `usuario_id`, `rol`, `materia_id`, `carrera_id`, `cohorte_id`, `desde`, `hasta`
- **THEN** el sistema crea la asignación con `tenant_id` del JWT, retorna 201 con `estado_vigencia` computado

#### Scenario: Asignación sin contexto académico (rol global de tenant)
- **WHEN** se crea una asignación con rol `ADMIN` sin `materia_id`, `carrera_id` ni `cohorte_id`
- **THEN** el sistema la crea correctamente; los campos de contexto son nullable

#### Scenario: FK de usuario en tenant diferente rechazada
- **WHEN** se intenta crear una asignación con un `usuario_id` que pertenece a un tenant diferente
- **THEN** el sistema retorna 404 (el usuario no existe en el scope del tenant del actor)

#### Scenario: Actor sin permiso recibe 403
- **WHEN** un actor sin permiso `equipos:asignar` intenta crear una asignación
- **THEN** el sistema retorna 403

### Requirement: estado_vigencia derivado de fechas de vigencia
El campo `estado_vigencia` de una asignación NO DEBE almacenarse en la base de datos. El sistema SHALL computarlo dinámicamente: `"Vigente"` si `desde <= date.today()` Y (`hasta IS NULL` O `date.today() <= hasta`); `"Vencida"` en cualquier otro caso.

#### Scenario: Asignación dentro del rango de vigencia
- **WHEN** se solicita una asignación cuya fecha `desde` ya pasó y `hasta` es futura o nula
- **THEN** el campo `estado_vigencia` en el response es `"Vigente"`

#### Scenario: Asignación con hasta en el pasado
- **WHEN** se solicita una asignación cuya fecha `hasta` ya pasó
- **THEN** el campo `estado_vigencia` en el response es `"Vencida"`

#### Scenario: Asignación futura (desde aún no llegó)
- **WHEN** se solicita una asignación cuya fecha `desde` es futura
- **THEN** el campo `estado_vigencia` en el response es `"Vencida"` (no está vigente aún)

### Requirement: Asignación vencida se conserva en histórico
Una asignación vencida NO DEBE ser eliminada del sistema. El sistema SHALL conservar todas las asignaciones históricas (vigentes y vencidas) en la base de datos (soft delete solo para eliminaciones explícitas). Las asignaciones vencidas NO otorgan permisos al usuario pero son consultables con filtros apropiados.

#### Scenario: Asignación vencida no otorga permisos
- **WHEN** el sistema resuelve los permisos efectivos de un usuario
- **THEN** solo las asignaciones con `estado_vigencia == "Vigente"` contribuyen permisos al usuario

#### Scenario: Historial de asignaciones consultable
- **WHEN** un actor con `equipos:asignar` solicita asignaciones con filtro `incluir_vencidas=true`
- **THEN** el sistema retorna tanto asignaciones vigentes como vencidas del tenant

### Requirement: Un usuario puede tener múltiples asignaciones simultáneas
El sistema SHALL permitir que un usuario tenga asignaciones simultáneas con distintos roles, en distintos contextos académicos y con distintos períodos de vigencia. No existe restricción de unicidad de asignación por usuario/rol/contexto.

#### Scenario: Múltiples roles simultáneos para el mismo usuario
- **WHEN** se crean dos asignaciones para el mismo usuario con roles distintos (ej: PROFESOR y TUTOR) en el mismo período
- **THEN** ambas asignaciones se crean exitosamente. Los permisos efectivos del usuario son la unión de los permisos de ambos roles.

#### Scenario: Mismo rol en contextos académicos distintos
- **WHEN** un PROFESOR tiene asignaciones en Materia A y en Materia B simultáneamente
- **THEN** el sistema las crea sin conflicto. El modificador `(propio)` limita el acceso a los datos de cada materia por separado.

### Requirement: Jerarquía de responsables vía responsable_id
El campo `responsable_id` de una asignación SHALL referenciar a un Usuario del mismo tenant (no a otra asignación). Representa al coordinador o supervisor directo del docente asignado. El campo es nullable (no toda asignación tiene supervisor explícito).

#### Scenario: Asignación con responsable válido
- **WHEN** se crea una asignación con `responsable_id` apuntando a un usuario existente del mismo tenant
- **THEN** la asignación se crea correctamente con la referencia de supervisión

#### Scenario: responsable_id en tenant diferente rechazado
- **WHEN** se intenta crear una asignación con `responsable_id` de un usuario de otro tenant
- **THEN** el sistema retorna 404 (el usuario no existe en el scope del tenant)

### Requirement: Listar asignaciones con filtros
El sistema SHALL listar asignaciones del tenant con filtros opcionales: `usuario_id`, `rol`, `materia_id`, `carrera_id`, `cohorte_id`, `estado_vigencia` (calculado, no filtrable directamente en DB — se filtra post-query o con expresión de fecha en WHERE). Paginación con `limit`/`offset`.

#### Scenario: Listado filtrado por usuario
- **WHEN** un actor con `equipos:asignar` solicita `GET /api/v1/asignaciones?usuario_id=<uuid>`
- **THEN** el sistema retorna solo las asignaciones del usuario especificado dentro del tenant

#### Scenario: Aislamiento multi-tenant en listado de asignaciones
- **WHEN** un actor del tenant A solicita `GET /api/v1/asignaciones`
- **THEN** solo se devuelven asignaciones del tenant A

### Requirement: Actualizar vigencia de asignación
El sistema SHALL permitir actualizar las fechas `desde` y/o `hasta` de una asignación existente. Solo los campos presentes en el body se actualizan.

#### Scenario: Actualización de fecha hasta
- **WHEN** un actor con `equipos:asignar` envía `PUT /api/v1/asignaciones/{id}` con nueva fecha `hasta`
- **THEN** el sistema actualiza la fecha y retorna 200 con `estado_vigencia` recalculado

### Requirement: Soft delete de asignación
El sistema SHALL implementar soft delete de asignaciones (setea `deleted_at`). Una asignación eliminada no aparece en listados activos pero se puede recuperar con `incluir_eliminadas=true` para auditoría.

#### Scenario: Soft delete de asignación activa
- **WHEN** un actor con `equipos:asignar` envía `DELETE /api/v1/asignaciones/{id}`
- **THEN** el sistema setea `deleted_at`, retorna 204. La asignación no aparece en listados normales.
