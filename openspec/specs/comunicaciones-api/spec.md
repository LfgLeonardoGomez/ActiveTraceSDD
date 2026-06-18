## ADDED Requirements

### Requirement: Preview de mensaje antes de encolar

The system SHALL expose `POST /api/comunicaciones/preview` that renders the message with substitution variables resolved for a list of recipients without persisting any data (RN-16).

The public placeholder syntax `{{alumno.nombre}}` and `{{alumno.email}}` MUST be accepted exactly as documented. Internally, before invoking `string.Template.substitute`, the service MUST normalize dotted key names to underscore-flat identifiers (`alumno.nombre` → `alumno_nombre`) in both the variable context dict and the template text. The public syntax contract MUST NOT change.

A placeholder that does not belong to the allowed set (`alumno_nombre`, `alumno_email`) MUST produce HTTP 422 with a message that names the unrecognized variable.

#### Scenario: Preview renders documented dot-notation variables correctly

- GIVEN a tenant with at least one alumno (nombre="Ana García", email="ana@example.com")
- WHEN a PROFESOR sends `POST /api/comunicaciones/preview` with `plantilla_asunto="Hola {{alumno.nombre}}"`, `plantilla_cuerpo="Tu email es {{alumno.email}}"`, and `destinatarios=[{alumno_id, nombre: "Ana García", email: "ana@example.com"}]`
- THEN the system returns HTTP 200 with `asunto="Hola Ana García"` and `cuerpo="Tu email es ana@example.com"` for that recipient
- AND no record is created in the `comunicacion` table

#### Scenario: Preview with multiple recipients — each message personalized

- GIVEN two alumnos: alumno A (nombre="Carlos", email="carlos@example.com") and alumno B (nombre="María", email="maria@example.com")
- WHEN a PROFESOR sends `POST /api/comunicaciones/preview` with both recipients and the template `"Hola {{alumno.nombre}}, te escribimos a {{alumno.email}}"`
- THEN the system returns exactly two rendered items: one with Carlos's data substituted and one with María's data substituted
- AND neither item contains any unresolved `{{...}}` placeholder

#### Scenario: Preview with unknown variable returns 422 with clear message

- GIVEN a valid authenticated PROFESOR
- WHEN the request body includes `plantilla_asunto="Hola {{alumno.inexistente}}"` with at least one recipient
- THEN the system returns HTTP 422
- AND the response body identifies `alumno.inexistente` (or its normalized form) as an unrecognized variable

#### Scenario: Preview does not persist data

- WHEN `POST /api/comunicaciones/preview` is called with valid data
- THEN no row is created in the `comunicacion` table and no entry is written to `AuditLog`

#### Scenario: Variable inválida en plantilla

- WHEN the template contains `{{variable_inexistente}}`
- THEN the system returns 422 indicating which variables are not available

### Requirement: Encolado masivo de comunicaciones
El sistema SHALL exponer `POST /api/comunicaciones/lote` para encolar uno o más mensajes en estado `Pendiente`, generando un `lote_id` compartido. Requiere permiso `comunicacion:enviar`.

#### Scenario: Encolado exitoso de lote
- **WHEN** el PROFESOR envía `{destinatarios: [...], plantilla_asunto, plantilla_cuerpo, materia_id}`
- **THEN** el sistema crea N registros `Comunicacion` en estado `Pendiente`, todos con el mismo `lote_id`, cifra cada `destinatario`, registra `COMUNICACION_ENVIAR` en auditoría y devuelve `{lote_id, total_encolados}`

#### Scenario: Encolado con tenant que requiere aprobación
- **WHEN** `Tenant.requiere_aprobacion_comunicaciones = True` y se encola un lote
- **THEN** el sistema crea los registros en `Pendiente` pero el worker no los procesa hasta aprobación; la respuesta incluye `requiere_aprobacion: true`

#### Scenario: Usuario sin permiso comunicacion:enviar
- **WHEN** un usuario sin `comunicacion:enviar` llama a `POST /api/comunicaciones/lote`
- **THEN** el sistema devuelve 403 Forbidden

#### Scenario: Scope propio del PROFESOR
- **WHEN** un PROFESOR encola mensajes para alumnos de una materia que no le pertenece
- **THEN** el sistema devuelve 403 Forbidden (validación de titularidad de asignación)

### Requirement: Consulta de estado de lote en tiempo real
El sistema SHALL exponer `GET /api/comunicaciones/lote/{lote_id}/estado` que devuelva el conteo de mensajes por estado del lote.

#### Scenario: Estado del lote con mensajes mixtos
- **WHEN** un lote tiene 10 mensajes: 3 Enviados, 5 Pendientes, 2 Error
- **THEN** el sistema devuelve `{lote_id, total: 10, pendiente: 5, enviando: 0, enviado: 3, error: 2, cancelado: 0}`

#### Scenario: Solo el creador del lote o un COORDINADOR puede consultar estado
- **WHEN** un PROFESOR intenta consultar el estado de un lote que no creó
- **THEN** el sistema devuelve 403 Forbidden

### Requirement: Aprobación o rechazo de lote
El sistema SHALL exponer `POST /api/comunicaciones/lote/{lote_id}/aprobar` y `POST /api/comunicaciones/lote/{lote_id}/cancelar` para usuarios con `comunicacion:aprobar` (RN-17).

#### Scenario: Aprobar lote completo
- **WHEN** un COORDINADOR con `comunicacion:aprobar` aprueba un lote
- **THEN** el sistema marca todos los mensajes `Pendiente` del lote como aprobados (campo `aprobado = True`) y registra `COMUNICACION_APROBAR` en auditoría

#### Scenario: Cancelar lote completo
- **WHEN** un usuario con `comunicacion:aprobar` cancela un lote
- **THEN** el sistema transiciona todos los mensajes `Pendiente` del lote a `Cancelado`

#### Scenario: Aprobación individual de mensaje
- **WHEN** un aprobador llama `POST /api/comunicaciones/{comunicacion_id}/aprobar`
- **THEN** solo ese mensaje queda aprobado; los demás del lote no se modifican

### Requirement: Cancelación de mensajes Pendiente
El sistema SHALL exponer `POST /api/comunicaciones/{comunicacion_id}/cancelar` para cancelar mensajes individuales en estado `Pendiente`.

#### Scenario: Cancelar mensaje propio Pendiente
- **WHEN** el PROFESOR que encoló el mensaje llama al endpoint de cancelación
- **THEN** el estado transiciona a `Cancelado`

#### Scenario: Cancelar mensaje ya Enviado
- **WHEN** se intenta cancelar un mensaje en estado `Enviado`
- **THEN** el sistema devuelve 422 indicando que la transición no es válida

### Requirement: Retry manual de mensajes con Error
El sistema SHALL exponer `POST /api/comunicaciones/{comunicacion_id}/retry` para volver a encolar un mensaje en estado `Error` cambiándolo a `Pendiente`.

#### Scenario: Retry de mensaje con Error
- **WHEN** un usuario con `comunicacion:enviar` llama al endpoint de retry sobre un mensaje en estado `Error`
- **THEN** el estado transiciona a `Pendiente` y el worker lo reintentará en el próximo ciclo

#### Scenario: Retry de mensaje en estado que no sea Error
- **WHEN** se intenta retry sobre un mensaje en estado `Enviado` o `Pendiente`
- **THEN** el sistema devuelve 422

### Requirement: Guard de permisos en endpoints de comunicaciones
El sistema SHALL aplicar guards precisos: `comunicacion:enviar` para crear y cancelar propios; `comunicacion:aprobar` para aprobar/rechazar lotes y cancelar cualquier mensaje del tenant.

#### Scenario: Aislamiento multi-tenant
- **WHEN** un usuario del Tenant A consulta o actúa sobre un lote del Tenant B
- **THEN** el sistema devuelve 404 (el lote no existe en el contexto del Tenant A)

### Requirement: Approval filter on get_pendientes_para_despacho

The system SHALL filter `get_pendientes_para_despacho` by `aprobado = True` in the SQL WHERE clause. This MUST apply regardless of tenant approval settings. The docstring MUST accurately describe the filter applied.

This requirement is defense-in-depth: the live dispatch path uses `get_todos_pendientes_elegibles` (which already filters correctly); this closes the trap for any future caller of the lower-level method.

**Hard rule**: multi-tenancy scoping via `BaseRepository` tenant filter remains unchanged. The `aprobado` predicate is an additional AND condition.

#### Scenario: get_pendientes_para_despacho excludes unapproved rows

- GIVEN a tenant with two `Comunicacion` rows in state `Pendiente`: one with `aprobado=True` and one with `aprobado=False`
- WHEN `get_pendientes_para_despacho` is called for that tenant
- THEN only the row with `aprobado=True` is returned
- AND the row with `aprobado=False` is absent from the result set

#### Scenario: get_pendientes_para_despacho respects tenant isolation

- GIVEN two tenants each with one `Pendiente`/`aprobado=True` comunicacion
- WHEN `get_pendientes_para_despacho` is called scoped to tenant A
- THEN only tenant A's row is returned (existing multi-tenancy guarantee, verified as unchanged)
