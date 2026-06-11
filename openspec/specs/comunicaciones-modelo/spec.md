## ADDED Requirements

### Requirement: Modelo Comunicacion con máquina de estados
El sistema SHALL persistir cada mensaje saliente como una entidad `Comunicacion` con los campos definidos en E-21 y un ciclo de vida estricto de estados (RN-15): `Pendiente → Enviando → Enviado | Error | Cancelado`. Solo las transiciones válidas están permitidas.

#### Scenario: Transición válida Pendiente → Enviando
- **WHEN** el worker toma un mensaje en estado `Pendiente` para procesar
- **THEN** el sistema transiciona el estado a `Enviando` antes de intentar el despacho

#### Scenario: Transición válida Enviando → Enviado
- **WHEN** el despacho vía N8N devuelve éxito (HTTP 2xx)
- **THEN** el sistema transiciona el estado a `Enviado` y registra `enviado_at`

#### Scenario: Transición válida Enviando → Error
- **WHEN** el despacho vía N8N falla (error HTTP o timeout)
- **THEN** el sistema transiciona el estado a `Error` y registra el motivo en `error_detalle`

#### Scenario: Transición válida Pendiente → Cancelado
- **WHEN** un usuario con `comunicacion:enviar` (para sus propios mensajes) o `comunicacion:aprobar` (para cualquier mensaje del tenant) cancela un mensaje en estado `Pendiente`
- **THEN** el sistema transiciona el estado a `Cancelado`

#### Scenario: Transición inválida rechazada
- **WHEN** se intenta transicionar desde `Enviado` o `Cancelado` a cualquier otro estado
- **THEN** el sistema lanza un error de dominio y NO persiste el cambio

### Requirement: Destinatario cifrado en reposo
El sistema SHALL cifrar el campo `destinatario` (email del alumno) con AES-256 al persistir la entidad `Comunicacion`. El valor descifrado NUNCA SHALL aparecer en logs, respuestas de API ni trazas de error.

#### Scenario: Persistencia con destinatario cifrado
- **WHEN** se encola un mensaje con `destinatario = "alumno@example.com"`
- **THEN** el valor almacenado en la columna `destinatario` es el texto cifrado, no el email en claro

#### Scenario: Descifrado solo en el worker al despachar
- **WHEN** el worker procesa un mensaje para enviarlo a N8N
- **THEN** el destinatario se descifra en memoria exclusivamente para construir el payload del webhook; no se expone en ningún otro contexto

### Requirement: Agrupación de envíos masivos por lote_id
El sistema SHALL asignar un `lote_id` (UUID) común a todos los mensajes generados en una misma operación de encolado. Los envíos individuales también tendrán un `lote_id` (lote de un solo elemento).

#### Scenario: Lote masivo con lote_id compartido
- **WHEN** se encolan 50 mensajes en una operación masiva
- **THEN** todos tienen el mismo `lote_id` y `enviado_por` del usuario autenticado

#### Scenario: Envío individual con lote_id propio
- **WHEN** se encola un único mensaje
- **THEN** el sistema genera un `lote_id` nuevo solo para ese mensaje

### Requirement: Migración de schema para tabla comunicacion
El sistema SHALL crear la tabla `comunicacion` mediante una migración Alembic con todos los campos de E-21: `id`, `tenant_id`, `enviado_por`, `materia_id`, `destinatario` (cifrado), `asunto`, `cuerpo`, `estado`, `lote_id`, `enviado_at`, `error_detalle`.

#### Scenario: Migración idempotente
- **WHEN** se ejecuta `alembic upgrade head` en una base con o sin la tabla
- **THEN** la migración se aplica sin error; una segunda ejecución no produce cambios

### Requirement: Flag de aprobación configurable por tenant
El sistema SHALL respetar el flag `Tenant.requiere_aprobacion_comunicaciones` al determinar si un lote puede ser procesado por el worker sin aprobación previa.

#### Scenario: Tenant sin aprobación requerida
- **WHEN** `requiere_aprobacion_comunicaciones = False` y se encola un lote
- **THEN** el worker puede tomar y despachar los mensajes `Pendiente` sin paso de aprobación

#### Scenario: Tenant con aprobación requerida
- **WHEN** `requiere_aprobacion_comunicaciones = True` y se encola un lote
- **THEN** los mensajes quedan en `Pendiente` y el worker NO los procesa hasta que un usuario con `comunicacion:aprobar` apruebe el lote
