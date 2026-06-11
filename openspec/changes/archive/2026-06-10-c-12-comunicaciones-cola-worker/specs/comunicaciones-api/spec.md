## ADDED Requirements

### Requirement: Preview de mensaje antes de encolar
El sistema SHALL exponer `POST /api/comunicaciones/preview` que renderice el mensaje con variables de sustitución resueltas para una lista de destinatarios sin persistir ningún dato (RN-16).

#### Scenario: Preview renderiza variables correctamente
- **WHEN** el PROFESOR envía `{plantilla_asunto: "Hola {{alumno.nombre}}", plantilla_cuerpo: "...", destinatarios: [{alumno_id, nombre, email}]}`
- **THEN** el sistema devuelve, por cada destinatario, el asunto y cuerpo con las variables resueltas

#### Scenario: Preview no persiste datos
- **WHEN** se llama `POST /api/comunicaciones/preview` con datos válidos
- **THEN** no se crea ningún registro en la tabla `comunicacion` ni en `AuditLog`

#### Scenario: Variable inválida en plantilla
- **WHEN** la plantilla contiene `{{variable_inexistente}}`
- **THEN** el sistema devuelve 422 indicando qué variables no están disponibles

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
