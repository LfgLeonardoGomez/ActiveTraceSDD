# Spec: equipos-bulk-operations

> Operaciones masivas sobre equipos docentes: asignación múltiple, clonación entre cohortes, actualización batch de vigencia y exportación a archivo.
> Todos los requisitos fueron añadidos en C-08 (equipos-docentes).

## ADDED Requirements

### Requirement: Asignación masiva de docentes
El sistema MUST proveer `POST /api/v1/equipos/asignacion-masiva` que cree múltiples asignaciones en una sola transacción. El payload define una tupla (materia_id, carrera_id, cohorte_id, rol, desde, hasta) y una lista de usuario_ids. El sistema SHALL crear una asignación por cada usuario_id en la lista. El batch está limitado a 100 asignaciones por request. Si cualquier usuario_id no existe en el tenant, el sistema debe rechazar toda la operación con 422 y no crear ninguna fila (atomicidad). Solo COORDINADOR y ADMIN con permiso `equipos:asignar` pueden ejecutarla.

#### Scenario: Asignación masiva exitosa de 10 docentes
- GIVEN 10 usuarios existentes en el tenant, materia X, carrera Y, cohorte Z
- WHEN un COORDINADOR envía `POST /api/v1/equipos/asignacion-masiva` con 10 usuario_ids y tupla común
- THEN el sistema crea 10 asignaciones en una transacción, retorna 201 con lista de asignaciones creadas y count=10

#### Scenario: Asignación masiva con usuario inexistente
- GIVEN 9 usuarios existentes y 1 usuario_id inexistente en el tenant
- WHEN un COORDINADOR envía el mismo payload
- THEN el sistema retorna 422 con detalle "usuario_id {uuid} no encontrado"; ninguna asignación se crea

#### Scenario: Asignación masiva excede límite de 100
- GIVEN 105 usuarios existentes en el tenant
- WHEN un COORDINADOR envía payload con 105 usuario_ids
- THEN el sistema retorna 422 con mensaje "Máximo 100 asignaciones por batch"

#### Scenario: Actor sin permiso recibe 403
- GIVEN un actor sin permiso `equipos:asignar`
- WHEN intenta enviar `POST /api/v1/equipos/asignacion-masiva`
- THEN el sistema retorna 403

### Requirement: Clonación de equipo entre cohortes
El sistema MUST proveer `POST /api/v1/equipos/clonar` que duplique todas las asignaciones vigentes (estado_vigencia = "Vigente") de un equipo origen (materia_id, carrera_id, cohorte_id) hacia un equipo destino (materia_id, carrera_id, cohorte_id_destino). Las nuevas asignaciones usan nuevas fechas de vigencia (`desde_nuevo`, `hasta_nuevo`). Las asignaciones originales NO se modifican. El endpoint debe retornar una vista previa (count de asignaciones a clonar) antes de ejecutar la operación. La operación real se ejecuta en una transacción atómica.

#### Scenario: Clonación exitosa con preview
- GIVEN un equipo origen con 5 asignaciones vigentes
- WHEN un COORDINADOR envía `POST /api/v1/equipos/clonar` con modo preview=true
- THEN el sistema retorna 200 con preview_count=5 y no modifica la base

#### Scenario: Ejecución de clonación
- GIVEN el mismo preview aceptado
- WHEN el COORDINADOR envía `POST /api/v1/equipos/clonar` con preview=false
- THEN el sistema crea 5 nuevas asignaciones con cohorte_id_destino y nuevas fechas; originales permanecen intactas

#### Scenario: Clonación sin asignaciones vigentes
- GIVEN un equipo origen sin asignaciones vigentes
- WHEN el COORDINADOR solicita clonar
- THEN el sistema retorna 422 con "No hay asignaciones vigentes para clonar"

#### Scenario: Clonación cross-tenant rechazada
- GIVEN un COORDINADOR del tenant A
- WHEN intenta clonar un equipo origen del tenant B
- THEN el sistema retorna 404 (no existe el equipo en el tenant)

### Requirement: Batch update de vigencia de equipo
El sistema MUST proveer `PUT /api/v1/equipos/{equipo_id}/vigencia` que actualice las fechas `desde` y `hasta` de todas las asignaciones vigentes de un equipo (materia × carrera × cohorte). La operación es atómica: todas las asignaciones se actualizan o ninguna. Si no hay asignaciones vigentes en el equipo, el sistema retorna 422. El endpoint requiere `equipos:asignar`.

#### Scenario: Batch vigencia exitoso
- GIVEN un equipo con 4 asignaciones vigentes
- WHEN un COORDINADOR envía `PUT /api/v1/equipos/{equipo_id}/vigencia` con nuevos desde/hasta
- THEN el sistema actualiza las 4 asignaciones y retorna 200 con count=4

#### Scenario: Batch vigencia sin asignaciones vigentes
- GIVEN un equipo donde todas las asignaciones están vencidas
- WHEN un COORDINADOR envía el mismo PUT
- THEN el sistema retorna 422 con "No hay asignaciones vigentes en el equipo"

#### Scenario: Batch vigencia sobre equipo inexistente
- GIVEN un equipo_id que no existe en el tenant
- WHEN un COORDINADOR envía el PUT
- THEN el sistema retorna 404

### Requirement: Exportar equipo a archivo
El sistema MUST proveer `GET /api/v1/equipos/exportar` que genere un archivo descargable (CSV por defecto; XLSX si `?format=xlsx`) con el detalle de todas las asignaciones de un equipo (materia × carrera × cohorte). Por defecto, el export excluye campos de PII (email, dni, cbu). Incluir PII requiere permiso `equipos:ver-pii`. El archivo debe respetar aislamiento multi-tenant.

#### Scenario: Export CSV con columnas por defecto
- GIVEN un equipo con 3 asignaciones
- WHEN un COORDINADOR envía `GET /api/v1/equipos/exportar?materia_id=X&carrera_id=Y&cohorte_id=Z`
- THEN el sistema retorna 200 con Content-Type text/csv; el archivo contiene nombre, apellidos, rol, materia, carrera, cohorte, comisiones, vigencia, estado_vigencia; NO contiene email, dni, cbu

#### Scenario: Export XLSX con PII
- GIVEN un COORDINADOR con permiso `equipos:ver-pii`
- WHEN envía `GET /api/v1/equipos/exportar?...&format=xlsx&include_pii=true`
- THEN el sistema retorna 200 con Content-Type application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; el archivo incluye email, dni, cbu

#### Scenario: Export sin permiso PII
- GIVEN un COORDINADOR sin permiso `equipos:ver-pii`
- WHEN envía `GET /api/v1/equipos/exportar?...&include_pii=true`
- THEN el sistema retorna 403

#### Scenario: Export sobre equipo vacío
- GIVEN un equipo sin asignaciones
- WHEN un COORDINADOR solicita exportar
- THEN el sistema retorna 200 con archivo CSV de encabezados vacío
