## ADDED Requirements

### Requirement: Endpoint de log completo paginado con filtros canónicos

El sistema SHALL exponer `GET /api/auditoria/log` que retorna registros del `audit_log` del tenant del usuario autenticado, paginados y filtrables. El endpoint SHALL aceptar query params: `fecha_desde` (ISO datetime), `fecha_hasta` (ISO datetime), `materia_id` (UUID opcional), `usuario_id` (UUID opcional — matchea `actor_id` O `impersonado_id`), `accion` (código de `AuditAction` opcional), `estado` (string opcional, filtra `detalle->>'estado'`), `page` (entero ≥1, default 1), `page_size` (entero entre 1 y 200, default 50). La respuesta SHALL ser `{items, total, page, pages}` con `items` ordenado por `fecha_hora.desc()`. Cada item SHALL exponer `{id, fecha_hora, actor_id, impersonado_id, materia_id, accion, categoria, detalle, filas_afectadas, ip, user_agent}`.

#### Scenario: Paginación default
- **GIVEN** un tenant con 75 registros de auditoría
- **WHEN** un ADMIN llama `GET /api/auditoria/log`
- **THEN** la respuesta es `{items: [50 elementos], total: 75, page: 1, pages: 2}`
- **AND** los items están ordenados por `fecha_hora.desc()`

#### Scenario: Página 2 con default page_size
- **WHEN** un ADMIN llama `GET /api/auditoria/log?page=2`
- **THEN** la respuesta contiene `items` con los 25 registros restantes y `page: 2, pages: 2`

#### Scenario: page_size mayor a 200 rechazado
- **WHEN** un ADMIN llama `GET /api/auditoria/log?page_size=201`
- **THEN** el sistema responde 422 con error de validación sobre `page_size`

#### Scenario: page_size = 0 rechazado
- **WHEN** un ADMIN llama `GET /api/auditoria/log?page_size=0`
- **THEN** el sistema responde 422 con error de validación

#### Scenario: Filtro por rango de fechas (inclusivo)
- **GIVEN** registros con `fecha_hora`: `2026-06-01 10:00`, `2026-06-05 12:00`, `2026-06-10 09:00`
- **WHEN** un ADMIN llama con `fecha_desde=2026-06-01T00:00:00Z&fecha_hasta=2026-06-05T23:59:59Z`
- **THEN** sólo se devuelven los 2 registros del 1 y 5 de junio (10 de junio queda fuera)

#### Scenario: Filtro por materia
- **WHEN** un ADMIN llama con `materia_id=M1`
- **THEN** sólo se devuelven registros cuya `materia_id = M1` (registros con `materia_id NULL` NO matchean)

#### Scenario: Filtro por usuario_id matchea actor o impersonado
- **GIVEN** un registro con `actor_id=U1, impersonado_id=NULL` y otro con `actor_id=ADMIN, impersonado_id=U1`
- **WHEN** un ADMIN llama con `usuario_id=U1`
- **THEN** ambos registros aparecen en la respuesta

#### Scenario: Filtro por código de acción del catálogo
- **WHEN** un ADMIN llama con `accion=PADRON_CARGAR`
- **THEN** sólo se devuelven registros cuya `accion = "PADRON_CARGAR"`

#### Scenario: Filtro por acción fuera del catálogo
- **WHEN** un ADMIN llama con `accion=ACCION_INEXISTENTE`
- **THEN** el sistema responde 422 (validación contra `AuditAction`)

#### Scenario: Filtro por estado vía detalle JSONB
- **GIVEN** un registro `COMUNICACION_ENVIAR` con `detalle = {"estado": "Enviado"}` y otro con `detalle = {"estado": "Error"}`
- **WHEN** un ADMIN llama con `estado=Enviado`
- **THEN** sólo se devuelve el primer registro

#### Scenario: Filtro por estado cuando el campo no existe en detalle
- **GIVEN** un registro con `detalle = NULL`
- **WHEN** un ADMIN llama con `estado=Enviado`
- **THEN** ese registro NO matchea (silent skip, sin error)

### Requirement: Scope `(propio)` aplicado al log completo para COORDINADOR

Cuando el `PermissionContext.is_propio == True`, el Service SHALL pasar `actor_filter = current_user.id` al repositorio y este SHALL agregar `WHERE (actor_id = :actor_filter OR impersonado_id = :actor_filter)` a TODAS las consultas. ADMIN y FINANZAS (`is_propio=False`) NO SHALL recibir ese filtro.

#### Scenario: COORDINADOR sólo ve registros propios
- **GIVEN** un COORDINADOR C1 con 4 registros propios (3 como actor, 1 como impersonado por un ADMIN) más 20 registros ajenos
- **WHEN** C1 llama `GET /api/auditoria/log`
- **THEN** la respuesta contiene exactamente 4 items
- **AND** todos los items tienen `actor_id == C1.id` O `impersonado_id == C1.id`

#### Scenario: COORDINADOR ve impersonación atribuida correctamente
- **GIVEN** un registro `COMUNICACION_ENVIAR` con `actor_id=ADMIN, impersonado_id=COORD` (un ADMIN impersonó al COORDINADOR)
- **WHEN** el COORDINADOR llama el endpoint
- **THEN** el registro aparece en la respuesta con ambos campos visibles para que el coordinador identifique la impersonación

#### Scenario: ADMIN ve todo el tenant
- **GIVEN** un ADMIN con `is_propio=False` y un tenant con 50 registros
- **WHEN** llama el endpoint sin filtros
- **THEN** la respuesta cuenta 50 items totales (paginados)

### Requirement: Inmutabilidad del log (RN-23) preservada por contrato de capability

La capability `auditoria-log-query` SHALL ser **exclusivamente read-only**. Ningún endpoint, service ni repository del scope `auditoria_*` SHALL exponer operaciones de INSERT, UPDATE o DELETE sobre `audit_log`. La inmutabilidad de C-05 (trigger DB) SHALL permanecer intacta.

#### Scenario: No existe endpoint de escritura
- **WHEN** se inspeccionan las rutas registradas bajo `/api/auditoria/`
- **THEN** ninguna ruta usa método POST, PUT, PATCH o DELETE

#### Scenario: Repositorio de log-query no tiene métodos de escritura
- **WHEN** se inspecciona la interfaz pública de `AuditoriaLogQueryRepository`
- **THEN** no existen métodos `insert`, `update`, `delete`, `add`, ni `flush`

### Requirement: Códigos de acción validados contra el catálogo cerrado (RN-24)

El schema del query param `accion` SHALL validar el valor contra el enum `AuditAction`. Códigos no presentes en el enum SHALL ser rechazados con 422 ANTES de ejecutar la query.

#### Scenario: Código válido del catálogo aceptado
- **WHEN** un ADMIN llama con `accion=LIQUIDACION_CERRAR`
- **THEN** el sistema acepta el parámetro y devuelve los registros filtrados

#### Scenario: Código arbitrario rechazado en validación
- **WHEN** un ADMIN llama con `accion=accion_inventada` o `accion=DROP_TABLE`
- **THEN** el sistema responde 422 sin ejecutar la query

### Requirement: Aislamiento multi-tenant en el log completo

El `AuditoriaLogQueryRepository` SHALL filtrar por `tenant_id` en todas sus consultas. Ningún registro de otro tenant SHALL aparecer en la respuesta, independientemente de los filtros aplicados.

#### Scenario: Tenant A no ve registros de Tenant B
- **GIVEN** Tenant A con 10 registros y Tenant B con 8 registros
- **WHEN** un ADMIN de Tenant A llama `GET /api/auditoria/log`
- **THEN** la respuesta tiene `total: 10`
- **AND** ningún `item.id` corresponde a un registro de Tenant B

#### Scenario: Filtro de usuario_id no cruza tenants
- **GIVEN** un usuario U1 que existe en Tenant A pero el filtro lo invoca un ADMIN de Tenant B
- **WHEN** el ADMIN de Tenant B llama con `usuario_id=U1.id`
- **THEN** la respuesta es `{items: [], total: 0}` (U1 no tiene registros en Tenant B)

### Requirement: Guard `auditoria:ver` fail-closed en el endpoint de log

El endpoint `GET /api/auditoria/log` SHALL declarar `require_permission("auditoria:ver")` como dependency. Sin el permiso explícito, el sistema SHALL responder 403.

#### Scenario: PROFESOR sin permiso recibe 403
- **GIVEN** un PROFESOR sin `auditoria:ver`
- **WHEN** llama `GET /api/auditoria/log`
- **THEN** el sistema responde 403
