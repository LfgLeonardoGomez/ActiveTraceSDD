# Delta for comunicaciones-worker

> Change: fix-comunicaciones-outbound · Domains modified: dispatch loop startup guard, resetear_colgados lifecycle
> Hard rules validated: state machine unchanged (no new transitions), PII AES-256 unchanged, no DB mocks.

---

## MODIFIED Requirements

### Requirement: N8N_WEBHOOK_URL no configurado — comportamiento del worker

The system MUST check for the presence of `N8N_WEBHOOK_URL` ONCE at dispatch loop startup, before entering the polling loop. If the URL is absent, the system MUST log exactly ONE message at level WARNING and MUST NOT enter the `while True` loop. No per-cycle log entry at any level SHALL be emitted for a missing webhook URL.

As defense-in-depth, any in-worker log call for a missing webhook URL MUST use WARNING level (not ERROR), ensuring that the missing-URL condition is never classified as a runtime error.

(Previously: the in-worker `run_once()` emitted `logger.error` on every invocation when `webhook_url is None`, producing ~2,880 ERROR/day. No "already warned" guard existed. The `_WEBHOOK_NOT_CONFIGURED` sentinel was defined but unused.)

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

---

### Requirement: Reseteo de mensajes colgados al iniciar el worker

The system SHALL perform `resetear_colgados` EXACTLY ONCE per worker process lifetime, during the startup phase before the polling loop begins. A dedicated `startup_run(db)` method on `ComunicacionWorker` SHALL encapsulate this call. The `run_once(db)` method MUST NOT invoke `resetear_colgados`.

(Previously: `run_once()` called `resetear_colgados` unconditionally on each invocation — a full-table `UPDATE … WHERE estado='Enviando'` + COMMIT every ~30 seconds. The spec says "al arrancar el worker" which means startup-only.)

#### Scenario: startup_run resets stuck messages once at startup

- GIVEN the worker process starts and there are `Comunicacion` rows in state `Enviando` older than the stale threshold
- WHEN `startup_run(db)` is called once before the loop
- THEN those rows are transitioned to `Pendiente`
- AND `resetear_colgados` is called exactly once across the worker's lifetime

#### Scenario: run_once does NOT call resetear_colgados

- GIVEN the worker is running its normal polling cycle
- WHEN `run_once(db)` is called M times (M >= 1) after startup
- THEN `resetear_colgados` is NOT invoked during any of those M calls

#### Scenario: Mensaje colgado en Enviando reseteado al arranque (unchanged)

- WHEN the worker starts and finds a message in `Enviando` with `updated_at` more than `COMUNICACION_STALE_THRESHOLD_MINUTES` minutes ago
- THEN the system transitions it to `Pendiente` for reprocessing in the next cycle

#### Scenario: Mensaje reciente en Enviando no se toca (unchanged)

- WHEN the worker starts and finds a message in `Enviando` with `updated_at` less than `COMUNICACION_STALE_THRESHOLD_MINUTES` minutes ago
- THEN the system leaves it in `Enviando`

---

## State Machine Non-Regression

The following requirement from the base spec is UNCHANGED by this change. It is listed here to make non-regression explicit.

### Requirement: Loop asíncrono de despacho de comunicaciones (unchanged)

The existing scenarios for worker processing eligible `Pendiente` messages, skipping unapproved messages, and the configurable polling interval remain intact. No transition in the state machine (`Pendiente → Enviando → Enviado | Error | Cancelado` / `Pendiente → Cancelado`) is modified by this change.

#### Scenario: State machine regression guard — Pendiente → Enviando → Enviado

- GIVEN a `Comunicacion` row in `Pendiente` with `aprobado=True` (or tenant with no approval required) and `N8N_WEBHOOK_URL` set
- WHEN the worker's `run_once` executes and N8N returns HTTP 2xx
- THEN the row transitions `Pendiente → Enviando → Enviado` with `enviado_at` populated

#### Scenario: State machine regression guard — Enviando → Error on N8N failure

- GIVEN a `Comunicacion` row transitions to `Enviando` and N8N returns a 5xx or times out
- WHEN the worker processes it
- THEN the row transitions to `Error` with `error_detalle` populated and the worker continues to the next message without raising
