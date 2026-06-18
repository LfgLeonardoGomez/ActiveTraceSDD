# Proposal: fix-comunicaciones-outbound

> Phase: SDD propose · Artifact store: hybrid (engram `sdd/fix-comunicaciones-outbound/proposal` + this file)
> Domain: outbound communications (C-12) · Governance: MEDIUM (implement with checkpoints)
> Delivery: no branching, no PRs · Language: English

## Intent (Why now)

Restore the outbound communications flow (template preview + batch enqueue) and clean up the dispatch worker: today template rendering returns HTTP 422 for the documented variable syntax (R-02, CRITICAL), so the feature is 100% broken, and the worker floods logs and over-writes the DB (R-08, R-14, R-17).

## Scope

### In scope
- **R-02 (CRITICAL)** — Fix template rendering so the documented public syntax `{{alumno.nombre}}` / `{{alumno.email}}` renders correctly; preserve the unknown-variable → 422 behavior.
- **R-08 (HIGH)** — Stop the worker from flooding logs every ~30s when `N8N_WEBHOOK_URL` is unset.
- **R-14 (MEDIUM)** — Run `resetear_colgados` once at worker startup, not every cycle.
- **R-17 (MEDIUM)** — Add the missing `aprobado` filter to `get_pendientes_para_despacho` (defense-in-depth on a dead-code path).
- Tests for all four fixes (real DB, no mocks; ephemeral Postgres).

### Out of scope
- Any change to the **public template syntax**. `{{alumno.nombre}}` stays as the user-facing contract (Decision A below).
- **Frontend changes.** Verified unnecessary (see Risk Resolution).
- Template engine replacement (Jinja2 / custom regex), new template variables, data migration.
- Any change to PII encryption, the state machine, multi-tenancy scoping, or the approval gate at `get_todos_pendientes_elegibles`.

## Chosen Approach (per fix)

### R-02 — Template rendering (Decision A: preserve public syntax)

**Decision (product-approved):** Keep the public placeholder syntax `{{alumno.nombre}}` exactly as documented. The KB (`knowledge-base/07_flujos_principales.md:64`) only requires "a per-student personalized message (subject + body)" and is agnostic about placeholder syntax; the concrete `{{alumno.nombre}}` syntax is the C-12 technical contract (archived spec + tests `tests/test_comunicaciones.py:191-192`). We honor that contract rather than break it.

**Mechanism:** `_renderizar_plantilla()` (`comunicacion_service.py:37,93,99-111`) currently maps `{{` → `${` and `}}` → `}`, producing `${alumno.nombre}`, which `string.Template` rejects because `.` is not a valid identifier char → `ValueError` → HTTP 422.

**Fix:** normalize dotted keys to flat identifiers BEFORE substitution, in both the variable map and the template text:
- `_VARIABLES_DISPONIBLES` and the context dict use flat keys (`alumno_nombre`, `alumno_email`).
- Normalization converts the public `{{alumno.nombre}}` to the internal `${alumno_nombre}` (dot → underscore) before calling `string.Template(...).substitute(...)`.
- Preserve the existing unknown-variable path: a placeholder not in the allowed set still raises HTTP 422 with a clear message.

**Why A over alternatives:** zero data migration (templates are never persisted — `crear_lote` stores the already-rendered `asunto`/`cuerpo`), preserves the documented contract, minimal diff, no new dependency. Custom regex (B) and Jinja2 (C) add surface area/dependencies for two variables. We explicitly DO NOT migrate to `{{alumno_nombre}}`: it would break the public contract the KB does not require us to change.

### R-08 — Worker log flood

Gate the missing-webhook check at loop startup in `_comunicacion_dispatch_loop` (`workers/main.py`): emit a single `logger.warning` and `return` from the coroutine before entering `while True`, so dispatch is cleanly disabled when `N8N_WEBHOOK_URL` is unset. As defense-in-depth, downgrade the in-worker `logger.error` (`comunicacion_worker.py:59-66`) to `logger.warning`. This eliminates the ~2,880 ERROR/day flood without masking genuine dispatch errors.

### R-14 — resetear_colgados at startup only

Extract a `startup_run(db)` method on `ComunicacionWorker` that performs `resetear_colgados` once. `_comunicacion_dispatch_loop` calls `startup_run` a single time before the loop; `run_once` no longer calls `resetear_colgados`. This matches the spec ("al arrancar el worker") and removes a full-table UPDATE + COMMIT every cycle.

### R-17 — Approval filter on dead-code path

Add `Comunicacion.aprobado.is_(True)` to the WHERE clause of `get_pendientes_para_despacho` (`comunicacion_repository.py:236-258`) and correct the docstring. The method is unused today (the worker uses `get_todos_pendientes_elegibles`, which filters correctly), but this closes a trap where any future caller would silently bypass the approval gate.

## Risk Resolution — Frontend variable-syntax check

**Question:** Does the frontend preview/compose component hardcode or reference `{{alumno.nombre}}`?

**Answer: No. Under Decision A, zero frontend changes are required.** Evidence:
- `frontend/src/features/comisiones/components/ComunicacionPreview.tsx:32-35` — the compose component calls the preview endpoint and renders the server-returned `asunto`/`cuerpo` verbatim into editable fields. It never constructs or references any `{{...}}` placeholder.
- `frontend/src/features/comisiones/components/ComunicacionesTab.tsx` and `ComunicacionTracking.tsx:257-296` — only display response DTO fields (`item.alumno_nombre`, `item.alumno_email`), which are data columns, not template variables.
- Repo-wide grep for `{{`, `alumno.nombre`, `alumno_nombre`, `plantilla`, `variables` across `frontend/src` found only JSX/style expressions and DTO field accesses — no template-placeholder strings.

The template literal originates server-side; the frontend only displays rendered output. Preserving the public syntax keeps the frontend untouched. (If a future change migrated to `{{alumno_nombre}}`, this would still hold because the frontend does not reference variable names — but that migration is out of scope.)

## Hard Rules (contract — unchanged by this change)
- **PII AES-256**: `destinatario` stays encrypted at `crear_lote`, decrypted in-memory only at dispatch. Not touched.
- **Multi-tenancy**: repository tenant scoping (`BaseRepository`, fail-closed) unchanged; R-17 only adds an `aprobado` predicate.
- **Approval gate mandatory before dispatch**: enforced at `get_todos_pendientes_elegibles`; R-17 extends the same guarantee to the dead-code path (defense-in-depth).
- **≤500 LOC per backend file**: all affected files stay well under the limit (`comunicacion_service.py` ~394, `comunicacion_worker.py` ~203, `comunicacion_repository.py` ~374).
- **No DB mocks**: all tests run against a real ephemeral Postgres.

## Governance
Outbound communications = **MEDIUM**. Implement with checkpoints; surface any non-obvious decision (e.g., worker startup session lifecycle) for review. No CRITICAL-domain code (auth, RBAC, audit, liquidaciones) is touched.

## Acceptance Criteria (high level)
1. A preview/enqueue request using `{{alumno.nombre}}` and `{{alumno.email}}` renders the substituted values (no 422).
2. An unknown placeholder still yields HTTP 422 with a clear message.
3. With `N8N_WEBHOOK_URL` unset, the dispatch loop logs a single WARNING and stops dispatching — no per-cycle ERROR flood.
4. `resetear_colgados` runs exactly once at worker startup; subsequent `run_once` cycles do not invoke it.
5. `get_pendientes_para_despacho` never returns rows with `aprobado=False`.
6. PII encryption, multi-tenancy scoping, the state machine, and the live approval gate are unchanged; coverage thresholds met (≥80% lines, ≥90% business rules).

## Next
`sdd-spec` and `sdd-design` (can run in parallel).
