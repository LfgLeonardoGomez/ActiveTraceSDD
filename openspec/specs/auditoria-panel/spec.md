## ADDED Requirements

### Requirement: Endpoint de acciones por día con filtros de rango y agrupación temporal

El sistema SHALL exponer `GET /api/auditoria/panel/acciones-por-dia` que retorna la cantidad de registros de auditoría por día UTC para el tenant del usuario autenticado. El endpoint SHALL aceptar query params `fecha_desde` (ISO date), `fecha_hasta` (ISO date), `materia_id` (UUID opcional), `usuario_id` (UUID opcional). El endpoint SHALL responder con `{items: [{fecha: date, total: int}], rango: {desde, hasta}}` ordenado por fecha ascendente. Si no se pasan fechas, el rango default SHALL ser los últimos 30 días desde `now()`.

#### Scenario: Conteo agrupado por día UTC
- **GIVEN** un tenant con 3 registros de auditoría con `fecha_hora` `2026-06-10`, 2 registros con `fecha_hora` `2026-06-11`
- **WHEN** un ADMIN llama `GET /api/auditoria/panel/acciones-por-dia?fecha_desde=2026-06-10&fecha_hasta=2026-06-11`
- **THEN** la respuesta es `{items: [{fecha: "2026-06-10", total: 3}, {fecha: "2026-06-11", total: 2}], rango: {desde: "2026-06-10", hasta: "2026-06-11"}}`

#### Scenario: Default de últimos 30 días
- **GIVEN** un tenant con registros de auditoría
- **WHEN** un ADMIN llama `GET /api/auditoria/panel/acciones-por-dia` sin parámetros de fecha
- **THEN** la respuesta cubre el rango `[now() - 30 días, now()]`
- **AND** el campo `rango` refleja ese rango calculado

#### Scenario: Filtro por materia
- **WHEN** un ADMIN llama el endpoint con `materia_id=<UUID-M1>`
- **THEN** sólo se cuentan registros donde `audit_log.materia_id = M1`

#### Scenario: Scope `(propio)` para COORDINADOR
- **GIVEN** un COORDINADOR con `is_propio=True` y dos registros propios (uno `actor_id=self.id`, otro `impersonado_id=self.id`) más cinco ajenos
- **WHEN** llama `GET /api/auditoria/panel/acciones-por-dia` cubriendo el mismo día
- **THEN** la respuesta cuenta exactamente 2 (los propios), no 7

#### Scenario: Aislamiento multi-tenant
- **GIVEN** Tenant A con 10 registros y Tenant B con 8 registros en el mismo día
- **WHEN** un ADMIN de Tenant A llama el endpoint
- **THEN** la respuesta cuenta 10 — ningún registro de Tenant B aparece

### Requirement: Endpoint de comunicaciones por docente agregado por estado

El sistema SHALL exponer `GET /api/auditoria/panel/comunicaciones-por-docente` que retorna por cada `actor_id` el conteo de `Comunicacion` agrupado por `estado` (Pendiente, Enviando, Enviado, Error, Cancelado). El endpoint SHALL aceptar query params `fecha_desde`, `fecha_hasta`, `materia_id`. La respuesta SHALL ser `{items: [{usuario_id, usuario_nombre, conteos: {Pendiente, Enviando, Enviado, Error, Cancelado}}]}`.

#### Scenario: Agregación por estado
- **GIVEN** un docente D1 con `Comunicacion`: 3 Enviado, 1 Error
- **WHEN** un ADMIN llama el endpoint
- **THEN** el item de D1 tiene `conteos: {Pendiente: 0, Enviando: 0, Enviado: 3, Error: 1, Cancelado: 0}`

#### Scenario: Filtros de rango y materia
- **WHEN** un ADMIN llama con `materia_id=M1` y `fecha_desde=D, fecha_hasta=D+7`
- **THEN** sólo se cuentan `Comunicacion` cuya `materia_id=M1` y `created_at` ∈ [D, D+7]

#### Scenario: Scope `(propio)` para COORDINADOR
- **GIVEN** un COORDINADOR C1 con 2 comunicaciones propias y otros docentes con comunicaciones ajenas
- **WHEN** C1 llama el endpoint con `is_propio=True`
- **THEN** la respuesta contiene exactamente un item: el de C1

### Requirement: Endpoint de interacciones por docente×materia con categorías inferidas

El sistema SHALL exponer `GET /api/auditoria/panel/interacciones-por-docente-materia` que cuenta registros de `audit_log` agrupados por `(actor_id, materia_id, accion)`. El endpoint SHALL aceptar query params `fecha_desde`, `fecha_hasta`, `materia_id` opcional, `usuario_id` opcional. La respuesta SHALL incluir el campo `categoria` calculado como el prefijo del código de acción (todo lo previo al primer `_`).

#### Scenario: Agrupación y categoría inferida
- **GIVEN** un tenant con registros: D1 / M1 / `CALIFICACIONES_IMPORTAR` x2, D1 / M1 / `COMUNICACION_ENVIAR` x5, D2 / M1 / `CALIFICACIONES_IMPORTAR` x1
- **WHEN** un ADMIN llama el endpoint
- **THEN** la respuesta contiene 3 items:
  - `{actor_id: D1, materia_id: M1, accion: "CALIFICACIONES_IMPORTAR", categoria: "CALIFICACIONES", total: 2}`
  - `{actor_id: D1, materia_id: M1, accion: "COMUNICACION_ENVIAR", categoria: "COMUNICACION", total: 5}`
  - `{actor_id: D2, materia_id: M1, accion: "CALIFICACIONES_IMPORTAR", categoria: "CALIFICACIONES", total: 1}`

#### Scenario: Acciones con `materia_id` NULL
- **GIVEN** un registro con `materia_id = NULL` (acción global, no asociada a materia)
- **WHEN** se invoca el endpoint sin filtro de materia
- **THEN** el item resultante tiene `materia_id: null`

### Requirement: Endpoint de últimas acciones con límite configurable

El sistema SHALL exponer `GET /api/auditoria/panel/ultimas-acciones` que retorna los últimos N registros de `audit_log` para el tenant, ordenados por `fecha_hora.desc()`. El parámetro `limit` SHALL tener default `200` y máximo `1000`. El endpoint SHALL aceptar filtros opcionales `materia_id`, `usuario_id`, `accion` (código del catálogo `AuditAction`). Cada item SHALL exponer `{id, fecha_hora, actor_id, impersonado_id, materia_id, accion, categoria, filas_afectadas, ip, user_agent}` (sin `detalle` por defecto — se obtiene desde el log completo).

#### Scenario: Default de 200 registros
- **GIVEN** un tenant con 500 registros
- **WHEN** un ADMIN llama `GET /api/auditoria/panel/ultimas-acciones` sin `limit`
- **THEN** la respuesta contiene 200 items ordenados por `fecha_hora.desc()`

#### Scenario: Límite configurable respetado
- **WHEN** un ADMIN llama el endpoint con `limit=50`
- **THEN** la respuesta contiene exactamente 50 items

#### Scenario: Límite máximo es 1000
- **WHEN** un ADMIN llama el endpoint con `limit=1001`
- **THEN** el sistema retorna 422 con mensaje de validación sobre `limit`

#### Scenario: Filtro por código de acción del catálogo
- **GIVEN** registros con varias acciones distintas
- **WHEN** un ADMIN llama con `accion=COMUNICACION_ENVIAR`
- **THEN** sólo se devuelven registros cuya `accion = COMUNICACION_ENVIAR`

#### Scenario: Filtro por acción inválida (fuera del catálogo)
- **WHEN** un ADMIN llama con `accion=INEXISTENTE_X`
- **THEN** el sistema retorna 422 (validación contra `AuditAction`)

### Requirement: Endpoint de catálogo de acciones derivado del enum AuditAction

El sistema SHALL exponer `GET /api/auditoria/catalogo-acciones` que retorna el listado de códigos válidos del enum `AuditAction` con su categoría inferida. Cada item SHALL ser `{codigo, categoria}`. El endpoint SHALL ser idempotente y NO consultar la base de datos.

#### Scenario: Catálogo expone todos los códigos del enum
- **WHEN** un ADMIN llama `GET /api/auditoria/catalogo-acciones`
- **THEN** la respuesta contiene un item por cada miembro del enum `AuditAction`
- **AND** cada item tiene `codigo` igual al valor del enum y `categoria` igual al prefijo antes del primer `_`

#### Scenario: Endpoint requiere `auditoria:ver`
- **GIVEN** un usuario sin el permiso `auditoria:ver`
- **WHEN** llama `GET /api/auditoria/catalogo-acciones`
- **THEN** el sistema responde 403

### Requirement: Guard `auditoria:ver` fail-closed en todos los endpoints del panel

Todos los endpoints bajo `/api/auditoria/panel/*` y `/api/auditoria/catalogo-acciones` SHALL declarar `require_permission("auditoria:ver")` como dependency. Sin el permiso explícito, el sistema SHALL responder 403.

#### Scenario: Usuario sin permiso recibe 403
- **GIVEN** un ALUMNO sin `auditoria:ver`
- **WHEN** llama cualquier endpoint del panel
- **THEN** el sistema responde 403 con mensaje "Permiso denegado"

#### Scenario: ADMIN ve el tenant completo (`is_propio=False`)
- **GIVEN** un ADMIN con `auditoria:ver` y `es_propio=False`
- **WHEN** llama `GET /api/auditoria/panel/acciones-por-dia`
- **THEN** el conteo incluye registros de todos los actores del tenant

#### Scenario: FINANZAS también accede al panel
- **GIVEN** un FINANZAS con `auditoria:ver` y `es_propio=False`
- **WHEN** llama cualquier endpoint del panel
- **THEN** el sistema responde 200 con datos agregados del tenant

### Requirement: Repository de panel es read-only y multi-tenant

El repositorio `AuditoriaPanelRepository` SHALL exponer **únicamente** métodos `get_*` / `count_*` que ejecutan SELECT. NO SHALL exponer ningún método que ejecute INSERT, UPDATE o DELETE. El constructor SHALL exigir `tenant_id != None` y todos los métodos SHALL filtrar por `audit_log.tenant_id = self.tenant_id`.

#### Scenario: Inicialización requiere tenant_id
- **WHEN** se construye `AuditoriaPanelRepository(db_session, tenant_id=None)`
- **THEN** el constructor lanza `ValueError("tenant_id is required")`

#### Scenario: Ningún método de escritura está expuesto
- **WHEN** se inspecciona la interfaz pública de `AuditoriaPanelRepository`
- **THEN** no existen métodos `insert`, `update`, `delete`, `add`, ni `flush`

#### Scenario: Todas las queries scoped a tenant
- **GIVEN** Tenant A con 10 registros y Tenant B con 8 registros
- **WHEN** se construye el repository con `tenant_id = A` y se ejecutan los métodos de conteo
- **THEN** ningún conteo incluye registros de Tenant B

---

### Requirement: UI — Gráfico de acciones por día (Frontend)

La UI SHALL displayar acciones por día como un gráfico de líneas (lazy-loaded).

#### Scenario: Líneas diarias
- **GIVEN** un ADMIN o COORDINADOR
- **WHEN** el panel carga
- **THEN** un gráfico de líneas muestra los conteos diarios

---

### Requirement: UI — Gráfico de comunicaciones por docente (Frontend)

La UI SHALL displayar estado de comunicaciones por docente como un stacked bar (lazy-loaded).

#### Scenario: Barras apiladas
- **GIVEN** un usuario
- **WHEN** el panel carga
- **THEN** un stacked bar muestra estados por docente

---

### Requirement: UI — Gráfico de interacciones por docente×materia (Frontend)

La UI SHALL displayar interacciones por docente y materia como un bar chart (lazy-loaded).

#### Scenario: Barras de interacciones
- **GIVEN** un usuario
- **WHEN** el panel carga
- **THEN** un gráfico muestra métricas por docente y materia

---

### Requirement: UI — Log de auditoría con filtros (Frontend)

La UI SHALL mostrar un log paginado con filtros por fecha, materia, usuario y estado.

#### Scenario: Filtro por fecha
- **GIVEN** un ADMIN
- **WHEN** se aplica un filtro de fecha
- **THEN** solo las entradas que coinciden se muestran

#### Scenario: COORDINADOR con scope propio
- **GIVEN** un COORDINADOR
- **WHEN** visualiza el log
- **THEN** solo las entradas de su scope propio se muestran

---

### Requirement: UI — Badge de scope (Frontend)

La UI SHALL mostrar "Vista personal" cuando COORDINADOR ve scope propio.

#### Scenario: Badge visible para COORDINADOR
- **GIVEN** un COORDINADOR
- **WHEN** el panel carga
- **THEN** un badge indica alcance restringido
