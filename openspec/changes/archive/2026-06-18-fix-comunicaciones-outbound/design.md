# Design: fix-comunicaciones-outbound

> Phase: SDD design · Artifact store: hybrid (engram `sdd/fix-comunicaciones-outbound/design` + this file)
> Domain: outbound communications (C-12) · Governance: MEDIUM · Language: English
> Reads: proposal (`sdd/fix-comunicaciones-outbound/proposal`), exploration.

## Architecture Approach

Four surgical fixes inside the existing `model → repository → service → worker` layering.
No new layer, no new dependency, no schema change, no migration, no frontend change.
Each fix is local to one function and is independently testable against a real ephemeral
Postgres. The chosen approach for R-02 (preserve public `{{alumno.nombre}}` syntax,
normalize dotted keys to flat identifiers internally before `string.Template`) is
ADR-001 below.

All names referenced here were confirmed by reading the real source:
- `backend/app/services/comunicacion_service.py` — `_renderizar_plantilla` (L85), `_VARIABLES_DISPONIBLES` (L37), normalization (L100), context dict (L102-105).
- `backend/app/workers/comunicacion_worker.py` — `run_once(self, db_session)` (L52), webhook check (L58-67), `resetear_colgados` call (L86), `_WEBHOOK_NOT_CONFIGURED` sentinel (L27, unused).
- `backend/app/workers/main.py` — `_comunicacion_dispatch_loop` (L36-65), `AsyncSessionLocal` (L53-58), interval (L49).
- `backend/app/repositories/comunicacion_repository.py` — `get_pendientes_para_despacho` (L236-258, no `aprobado` filter), `get_todos_pendientes_elegibles` (L264-287, has `Comunicacion.aprobado.is_(True)` at L280), `resetear_colgados(self, stale_threshold_minutes: int) -> int` (L348).

---

## R-02 — Template rendering normalization (CRITICAL)

### Root cause (confirmed)
`_renderizar_plantilla` (L99-111) does `plantilla.replace("{{", "${").replace("}}", "}")`,
producing `${alumno.nombre}`. `string.Template` placeholders are `[_a-zA-Z][_a-zA-Z0-9]*`,
so the `.` ends the identifier; `${alumno.nombre}` is read as placeholder `alumno` followed
by literal `.nombre`. With the context dict keyed `"alumno.nombre"` (not `"alumno"`),
`substitute` raises `KeyError: 'alumno'` → caught at L112 → HTTP 422. Every documented
preview/enqueue call fails.

### Normalization algorithm (exact)

Introduce a single, total, **injective** key transform and apply it in BOTH directions
(template text and value dict) so they always agree:

```python
def _normalize_key(public_key: str) -> str:
    # "alumno.nombre" -> "alumno_nombre"  (dot -> underscore)
    return public_key.replace(".", "_")
```

Injectivity: the only allowed public keys are `{"alumno.nombre", "alumno.email"}`
(`_VARIABLES_DISPONIBLES`). Neither contains an underscore, so `.` → `_` cannot collide
two distinct allowed keys onto the same flat key (`alumno_nombre` ≠ `alumno_email`).
The transform is injective over the allowed domain. (Documented as a constraint in the
code: if a future variable name itself contained `_`, the inverse below would be ambiguous —
acceptable because the allowed set is closed and validated.)

Three coordinated edits inside `_renderizar_plantilla`:

1. **Template text**: convert public `{{alumno.nombre}}` directly to the internal
   `${alumno_nombre}`. Do it in one pass over the placeholder bodies rather than a blind
   global `.` → `_` (which would corrupt literal dots in prose). Concretely, after the
   existing `{{`/`}}` → `${`/`}` conversion, rewrite only the identifiers inside `${...}`:

   ```python
   import re
   _PLACEHOLDER = re.compile(r"\$\{([^}]*)\}")

   normalizada = plantilla.replace("{{", "${").replace("}}", "}")
   normalizada = _PLACEHOLDER.sub(
       lambda m: "${" + m.group(1).strip().replace(".", "_") + "}",
       normalizada,
   )
   ```

   This guarantees literal dots in body prose (e.g. "Saludos. Atte.") are never touched —
   only characters between `${` and `}` are normalized.

2. **Value dict**: build it with flat keys so it matches the rewritten template:

   ```python
   variables_contexto = {
       _normalize_key("alumno.nombre"): nombre,   # "alumno_nombre"
       _normalize_key("alumno.email"): email,     # "alumno_email"
   }
   ```

3. **`_VARIABLES_DISPONIBLES`**: keep it as the **public-facing** set
   `{"alumno.nombre", "alumno.email"}` (it is only used to build the human-readable 422
   message at L118, which should show the public syntax the user typed). No change to its
   value; it stays the documented contract surface.

### Unknown-variable → 422 (preserved, confirmed mechanism)

Today detection is implicit: `string.Template.substitute` raises `KeyError` for any
placeholder absent from the value dict (there is NO explicit allow-set check before
substitution). After the fix this still holds — an unknown public placeholder like
`{{alumno.telefono}}` normalizes to `${alumno_telefono}`, which is not a key in
`variables_contexto`, so `substitute` raises `KeyError('alumno_telefono')` → re-raised as
HTTP 422 at L112-120. We keep the existing `try/except KeyError`/`except ValueError`
structure verbatim; only the dict keys and the template rewrite change.

One refinement to the 422 message: today it prints the raw `KeyError` key
(`str(exc).strip("'")`), which post-fix would be the flat key `alumno_telefono`. To keep
the message aligned with the public syntax the user typed, map the flat key back for display:

```python
except KeyError as exc:
    flat = str(exc).strip("'")
    publica = flat.replace("_", ".", 1)  # display-only, best-effort
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=(
            f"Variable de plantilla '{publica}' no disponible. "
            f"Variables permitidas: {sorted(_VARIABLES_DISPONIBLES)}"
        ),
    ) from exc
```

`replace("_", ".", 1)` only affects the displayed message, never matching logic, so the
non-injective inverse (for hypothetical underscore-containing names) is harmless here.

### Why this over alternatives
ADR-001 (below) records the decision. Net: zero migration (templates are never persisted —
`crear_lote` stores already-rendered `asunto`/`cuerpo`), preserves the documented public
contract and existing tests at `tests/test_comunicaciones.py:191-192`, no new dependency,
diff confined to one method.

---

## R-08 — Worker log-flood gate at loop startup (HIGH)

### Current placement (confirmed)
The missing-webhook check is inside `run_once` (`comunicacion_worker.py` L58-67) and emits
`logger.error` on every pass. `_comunicacion_dispatch_loop` (`main.py` L51-65) calls
`run_once` every `interval` (default 30s) → ~2,880 ERROR/day. The `_WEBHOOK_NOT_CONFIGURED`
sentinel (L27) is dead.

### Design
Move the decision to **loop startup**, before `while True`, in `_comunicacion_dispatch_loop`:

```python
async def _comunicacion_dispatch_loop() -> None:
    settings = Settings()
    if not settings.n8n_webhook_url:
        logger.warning(
            "comunicacion_dispatch_disabled_no_webhook",
            extra={"event": "dispatch_disabled", "reason": "N8N_WEBHOOK_URL unset"},
        )
        return  # coroutine exits cleanly; gather() keeps padron loop alive
    worker = ComunicacionWorker(...)  # unchanged construction
    interval = settings.comunicacion_dispatch_interval_seconds
    # startup_run once (see R-14), then while True: ...
```

`run_once(self, db_session)` keeps its current signature. Inside `run_once`, **downgrade**
the in-worker guard (L60 `logger.error` → `logger.warning`) as defense-in-depth so that any
path that still reaches `run_once` with no webhook warns instead of erroring, and `return`s.
The early loop return means the per-cycle path is normally never hit. The `_WEBHOOK_NOT_CONFIGURED`
sentinel stays unused (out of scope to remove; harmless).

Result: exactly one WARNING at startup when the webhook is unset, then the coroutine ends;
`asyncio.gather` in `main()` continues running `_padron_sync_loop`.

---

## R-14 — `startup_run` once at worker startup (MEDIUM)

### Current behavior (confirmed)
`run_once` calls `repo_global.resetear_colgados(...)` unconditionally every cycle
(`comunicacion_worker.py` L86), i.e. a full-table `UPDATE ... WHERE estado='Enviando'` +
COMMIT every 30s. Spec says startup-only.

### Design — new method + lifecycle

Add `startup_run` to `ComunicacionWorker`; remove the `resetear_colgados` block from
`run_once` (L85-91):

```python
async def startup_run(self, db_session: Any) -> int:
    """Run once at worker startup: reset stale 'Enviando' messages. Returns count."""
    if not self.webhook_url:
        return 0
    from uuid import UUID as _UUID
    _FAKE_TENANT = _UUID("00000000-0000-0000-0000-000000000001")
    repo_global = _GlobalComunicacionRepository(db_session, _FAKE_TENANT)
    reseteados = await repo_global.resetear_colgados(self.stale_threshold_minutes)
    if reseteados > 0:
        logger.info(
            "comunicacion_worker_reset_colgados",
            extra={"event": "reset_colgados", "count": reseteados},
        )
    return reseteados
```

Session lifecycle in `_comunicacion_dispatch_loop` (after the R-08 gate, before `while True`):

```python
from app.core.database import AsyncSessionLocal
if AsyncSessionLocal is not None:
    startup_session = AsyncSessionLocal()
    try:
        await worker.startup_run(startup_session)
    finally:
        await startup_session.close()
# then: while True: ... worker.run_once(db_session) ...
```

`startup_run` uses the same `AsyncSessionLocal` pattern the loop already uses (L53-58),
in a dedicated short-lived session created and closed once. `run_once` no longer creates
`_GlobalComunicacionRepository` for reset purposes; it keeps its own `repo_global` only for
`get_todos_pendientes_elegibles` + dispatch (L94+ unchanged). The full-table UPDATE happens
exactly once per process start.

Edge case: if `AsyncSessionLocal` is `None` at startup (DB not ready), skip `startup_run`
(stale reset is best-effort recovery, not correctness-critical) and proceed to the loop,
where the existing `AsyncSessionLocal is None` guard (L54-57) already handles per-cycle
not-ready states.

---

## R-17 — Approval filter on dead-code path (MEDIUM)

### Confirmed
`get_pendientes_para_despacho` (`comunicacion_repository.py` L247-256) WHERE clause has
`tenant_id`, `estado == pendiente`, `deleted_at.is_(None)` — but **no** `aprobado` filter,
contradicting its own docstring (L241). The live worker uses
`get_todos_pendientes_elegibles`, which correctly includes `Comunicacion.aprobado.is_(True)`
(L280). This method is dead today but is a trap.

### Design — exact change
Copy the proven predicate from the sibling method into the WHERE clause:

```python
.where(
    Comunicacion.tenant_id == self.tenant_id,
    Comunicacion.estado == EstadoComunicacion.pendiente.value,
    Comunicacion.aprobado.is_(True),          # <-- added
    Comunicacion.deleted_at.is_(None),
)
```

And correct the docstring to state the real semantics (drop the "OR tenant no requiere
aprobación" clause, since tenants without approval already have `aprobado=True` set at
enqueue by the service — same invariant documented at L270-272 of the sibling method):

> Elegible = Pendiente + aprobado=True + no soft-deleted (scoped al tenant actual).

One-line predicate + docstring; no behavior change for live code (method unused), pure
defense-in-depth.

---

## Test Design (real DB, no mocks)

Ephemeral Postgres on port 5433:
`DATABASE_URL=postgresql+asyncpg://trace_user:trace_pass@localhost:5433/activia_trace`.
Existing suite: `backend/tests/test_comunicaciones.py` (service tests use the `db_session`
fixture against the real DB; helpers `_crear_tenant`, `_crear_usuario`, `_make_service`,
`_perm_enviar` already present).

### R-02 (real data, service-level)
- **Happy path (fixes 8.2 / 8.3, currently failing)**: `test_preview_renderiza_variables`
  with `plantilla_asunto="Hola {{alumno.nombre}}"`, `plantilla_cuerpo="Tu email es {{alumno.email}}"`
  → asserts `"Hola Juan Pérez"` / `"Tu email es juan@example.com"` (assertions already at
  L199-200 — they pass once the normalization lands).
- **Triangulation**: `test_preview_renderiza_multiples_destinatarios` (already present)
  confirms per-destinatario isolation.
- **Literal-dot safety (new)**: body `"Saludos. {{alumno.nombre}}. Atte."` → asserts the
  prose dots survive and only the placeholder is substituted. Guards the regex-scoped rewrite.
- **Unknown variable → 422 (new)**: `plantilla_cuerpo="{{alumno.telefono}}"` → assert
  `HTTPException` with `status_code == 422` and message mentioning `alumno.telefono`
  (public syntax) and the allowed set. No DB write needed (preview is read-only).

### R-08 (caplog, no DB needed for the gate)
- **Loop gate (new)**: call `_comunicacion_dispatch_loop` with `settings.n8n_webhook_url`
  unset (patch `Settings` or env) and assert via `caplog.at_level(logging.WARNING)` exactly
  one WARNING record (`dispatch_disabled`) and that the coroutine returns without entering
  the loop (it must complete; assert it does not `await asyncio.sleep` — e.g. wrap in
  `asyncio.wait_for(..., timeout=0.1)` and expect normal completion, not TimeoutError).
- **In-worker downgrade (new)**: `ComunicacionWorker(webhook_url=None).run_once(db_session)`
  called N=3 times; assert `caplog` shows WARNING (not ERROR) and no records escalate.

### R-14 (call-count, real DB)
- **startup resets, cycles don't (new)**: seed one `Comunicacion` stuck in `Enviando` with
  `updated_at` older than `stale_threshold_minutes` (real insert via repo/model). Call
  `worker.startup_run(db_session)` → assert return count `== 1` and the row is back to
  `Pendiente`. Then seed a second stale row and call `run_once(db_session)` twice → assert
  the second stale row remains `Enviando` (i.e. `run_once` no longer resets). Use real rows;
  no mock. (A spy/counter on `resetear_colgados` via `unittest.mock.patch.object` on the
  repo method is acceptable to assert call count without mocking the DB itself — the DB query
  still runs in `startup_run`.)

### R-17 (real data, repository-level)
- **Excludes aprobado=False (new)**: insert two `Pendiente` rows in the same tenant, one
  `aprobado=True`, one `aprobado=False`. Call
  `ComunicacionRepository(db, tenant_id).get_pendientes_para_despacho(10)` → assert only the
  approved row is returned. Real rows, real query.

Coverage: these add ~5 tests + repair 2; keep ≥80% lines / ≥90% business-rule coverage.

---

## File-level Change Plan (LOC confirmed under 500)

| File | Current LOC | Change | Est. delta | Post LOC |
|---|---|---|---|---|
| `backend/app/services/comunicacion_service.py` | 395 | R-02: add `_normalize_key` + `_PLACEHOLDER` regex, rewrite placeholder bodies, flat value-dict keys, display-only key un-flatten in 422 | +12 | ~407 |
| `backend/app/workers/comunicacion_worker.py` | 203 | R-08: error→warning in `run_once` guard; R-14: add `startup_run`, remove per-cycle reset block from `run_once` | +14 / -6 net +8 | ~211 |
| `backend/app/workers/main.py` | 83 | R-08: startup webhook gate + return; R-14: call `startup_run` once before loop | +14 | ~97 |
| `backend/app/repositories/comunicacion_repository.py` | ~374 | R-17: add `aprobado.is_(True)` predicate + docstring fix | +1 / docstring | ~375 |
| `backend/tests/test_comunicaciones.py` | (existing) | repair 8.2/8.3, add ~5 tests (literal-dot, unknown-var, loop gate, in-worker downgrade, startup-vs-cycle, R-17 filter) | +~90 | well under 500 |

All four production files stay comfortably below the 500-LOC hard rule.

---

## ADR-001 — Preserve public `{{alumno.nombre}}` syntax; normalize internally

- **Status**: Accepted (product-approved in proposal, Decision A).
- **Context**: `string.Template` rejects dotted placeholders; the documented public
  contract and archived C-12 spec + tests use `{{alumno.nombre}}`.
- **Decision**: Keep the public dotted syntax. Internally normalize dotted keys to flat
  identifiers (`.` → `_`), scoped strictly to placeholder bodies, in both the template text
  and the value dict, before `string.Template.substitute`.
- **Consequences**: Zero migration (templates never persisted), zero frontend change,
  existing tests preserved, no new dependency. Diff confined to `_renderizar_plantilla`.
- **Rejected**:
  - **B — custom regex render engine for dotted notation**: a hand-rolled substitution
    engine is more surface area / custom bugs for two variables; rejected.
  - **C — Jinja2 (sandboxed)**: new dependency and feature surface vastly larger than two
    variables warrant; rejected.
  - **D — migrate public syntax to `{{alumno_nombre}}`**: would break the documented C-12
    contract and archived tests for no KB-required benefit; out of scope, rejected.

## ADR-002 — Worker dispatch gate at coroutine startup, not per cycle

- **Status**: Accepted.
- **Context**: per-cycle webhook check floods logs (~2,880 ERROR/day) and per-cycle
  `resetear_colgados` issues a needless full-table UPDATE every 30s.
- **Decision**: Decide dispatch-enabled once at `_comunicacion_dispatch_loop` startup
  (warn + `return` if no webhook); run `resetear_colgados` once via a dedicated
  `startup_run` before the loop. `run_once` becomes pure per-cycle dispatch.
- **Consequences**: One WARNING instead of a flood; one full-table UPDATE per process start;
  `asyncio.gather` keeps the padron loop alive when dispatch is disabled. One extra
  short-lived session at startup (acceptable).
- **Rejected**: an "already-warned" boolean flag inside `run_once` (keeps the per-cycle
  branch and the dead sentinel; less clean than gating at the loop boundary).

---

## Open Design Points

1. **Display-only un-flatten in the 422 message** (`replace("_", ".", 1)`) is best-effort
   and only cosmetic. If a future variable name contains an underscore the displayed public
   key could be slightly off; matching logic is unaffected. Acceptable given the closed,
   validated allowed set. Flagged for the tasks phase as a known cosmetic limitation, not a
   correctness risk.
2. **`_WEBHOOK_NOT_CONFIGURED` sentinel (L27)** stays unused after the fix. Removing it is
   trivial cleanup but strictly out of scope; leave or remove at tasks-phase discretion.
3. **Startup-run when DB not ready**: design skips stale-reset if `AsyncSessionLocal is None`
   at startup. This is intentional (best-effort recovery), but confirm in tasks that the
   first real `run_once` cycle does not depend on a prior successful `startup_run`.

## Next
`sdd-tasks` (after spec is also ready).
