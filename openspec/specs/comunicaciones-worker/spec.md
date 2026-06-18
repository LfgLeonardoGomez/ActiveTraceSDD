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

### Requirement: N8N_WEBHOOK_URL no configurado — comportamiento del worker

The system MUST check for the presence of `N8N_WEBHOOK_URL` ONCE at dispatch loop startup, before entering the polling loop. If the URL is absent, the system MUST log exactly ONE message at level WARNING and MUST NOT enter the `while True` loop. No per-cycle log entry at any level SHALL be emitted for a missing webhook URL.

As defense-in-depth, any in-worker log call for a missing webhook URL MUST use WARNING level (not ERROR), ensuring that the missing-URL condition is never classified as a runtime error.

#### Scenario: Dispatch loop with N8N_WEBHOOK_URL unset — single WARNING, no loop entered

- GIVEN `N8N_WEBHOOK_URL` is not set in the environment
- WHEN `_comunicacion_dispatch_loop` is invoked N times (e.g., across N scheduler ticks)
- THEN exactly ONE WARNING log entry is emitted for the missing webhook condition
- AND no ERROR log entry is emitted for this condition
- AND no `Comunicacion` row transitions to `Enviando`

#### Scenario: Dispatch loop with N8N_WEBHOOK_URL set — normal operation

- GIVEN `N8N_WEBHOOK_URL` is set to a valid URL
- WHEN `_comunicacion_dispatch_loop` starts
- THEN no warning about missing webhook is emitted and the loop enters its normal polling cycle

### Requirement: Reseteo de mensajes colgados al iniciar el worker

The system SHALL perform `resetear_colgados` EXACTLY ONCE per worker process lifetime, during the startup phase before the polling loop begins. A dedicated `startup_run(db)` method on `ComunicacionWorker` SHALL encapsulate this call. The `run_once(db)` method MUST NOT invoke `resetear_colgados`.

#### Scenario: startup_run resets stuck messages once at startup

- GIVEN the worker process starts and there are `Comunicacion` rows in state `Enviando` older than the stale threshold
- WHEN `startup_run(db)` is called once before the loop
- THEN those rows are transitioned to `Pendiente`
- AND `resetear_colgados` is called exactly once across the worker's lifetime

#### Scenario: run_once does NOT call resetear_colgados

- GIVEN the worker is running its normal polling cycle
- WHEN `run_once(db)` is called M times (M >= 1) after startup
- THEN `resetear_colgados` is NOT invoked during any of those M calls

#### Scenario: Mensaje colgado en Enviando reseteado al arranque

- WHEN the worker starts and finds a message in `Enviando` with `updated_at` more than `COMUNICACION_STALE_THRESHOLD_MINUTES` minutes ago
- THEN the system transitions it to `Pendiente` for reprocessing in the next cycle

#### Scenario: Mensaje reciente en Enviando no se toca

- WHEN the worker starts and finds a message in `Enviando` with `updated_at` less than `COMUNICACION_STALE_THRESHOLD_MINUTES` minutes ago
- THEN the system leaves it in `Enviando`

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
