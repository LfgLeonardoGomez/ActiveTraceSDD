## ADDED Requirements

### Requirement: Loop asíncrono de despacho de comunicaciones
El sistema SHALL ejecutar un loop periódico en `workers/main.py` que procese mensajes `Comunicacion` en estado `Pendiente` y aprobados (o sin requerimiento de aprobación según el tenant).

#### Scenario: Worker procesa mensajes Pendiente elegibles
- **WHEN** hay mensajes en estado `Pendiente` con `aprobado = True` (o `requiere_aprobacion_comunicaciones = False` para su tenant)
- **THEN** el worker los transiciona a `Enviando` y los despacha vía N8N

#### Scenario: Worker no procesa mensajes que requieren aprobación pendiente
- **WHEN** hay mensajes en estado `Pendiente` en un tenant con `requiere_aprobacion_comunicaciones = True` y sin `aprobado = True`
- **THEN** el worker los ignora hasta que sean aprobados

#### Scenario: Ciclo de polling configurable
- **WHEN** el worker arranca
- **THEN** el intervalo entre ciclos es `COMUNICACION_DISPATCH_INTERVAL_SECONDS` (default 30 segundos)

### Requirement: Integración con N8N para despacho
El sistema SHALL delegar el envío real del email a N8N mediante `POST {N8N_WEBHOOK_URL}` con payload `{destinatario, asunto, cuerpo}`. El `destinatario` SHALL ser descifrado en memoria exclusivamente para construir este payload.

#### Scenario: Despacho exitoso vía N8N
- **WHEN** el webhook de N8N devuelve HTTP 2xx
- **THEN** el sistema transiciona el mensaje a `Enviado`, registra `enviado_at` y el despacho se considera exitoso

#### Scenario: Fallo del webhook de N8N
- **WHEN** el webhook de N8N devuelve error HTTP (4xx/5xx) o expira el timeout
- **THEN** el sistema transiciona el mensaje a `Error`, registra el motivo en `error_detalle` y continúa con el siguiente mensaje del lote sin bloquear

#### Scenario: N8N_WEBHOOK_URL no configurado
- **WHEN** `N8N_WEBHOOK_URL` no está definida en el entorno
- **THEN** el worker registra un error crítico en el log y NO toma mensajes para procesar (evita transicionar a `Enviando` sin poder despachar)

### Requirement: Reseteo de mensajes colgados al iniciar el worker
El sistema SHALL, al arrancar el worker, resetear a `Pendiente` todos los mensajes que estén en estado `Enviando` desde hace más de `COMUNICACION_STALE_THRESHOLD_MINUTES` minutos (default 10).

#### Scenario: Mensaje colgado en Enviando reseteado al arranque
- **WHEN** el worker arranca y encuentra un mensaje en `Enviando` con `updated_at` hace más de 10 minutos
- **THEN** el sistema lo transiciona a `Pendiente` para que sea reprocesado en el próximo ciclo

#### Scenario: Mensaje reciente en Enviando no se toca
- **WHEN** el worker arranca y encuentra un mensaje en `Enviando` con `updated_at` hace menos de 10 minutos
- **THEN** el sistema lo deja en `Enviando` (puede estar siendo procesado por otro ciclo)

### Requirement: N8NClient como capa de integración aislada
El sistema SHALL encapsular la comunicación con N8N en `integrations/n8n_client.py`. Esta clase SHALL ser inyectable (instanciada con `webhook_url`) para permitir mocking en tests.

#### Scenario: N8NClient mockeable en tests
- **WHEN** los tests del worker instancian `N8NClient` con una URL de test
- **THEN** pueden interceptar el HTTP POST sin necesidad de una instancia real de N8N

#### Scenario: Timeout configurable de N8N
- **WHEN** el webhook de N8N no responde en `N8N_TIMEOUT_SECONDS` (default 10)
- **THEN** el cliente lanza `N8NTimeoutError` que el worker captura y registra como `Error`

### Requirement: Procesamiento por lotes (batch) en el worker
El sistema SHALL procesar mensajes en lotes de tamaño configurable (`COMUNICACION_BATCH_SIZE`, default 50) por ciclo para evitar saturar N8N o la DB.

#### Scenario: Worker procesa máximo BATCH_SIZE por ciclo
- **WHEN** hay 200 mensajes elegibles en la DB
- **THEN** el worker toma solo los primeros 50 (o el valor configurado), los despacha y espera el siguiente ciclo para los siguientes
