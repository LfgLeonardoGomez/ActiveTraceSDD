# Exploration: fix-comunicaciones-outbound

> Phase: SDD explore · Artifact store: hybrid (engram `sdd/fix-comunicaciones-outbound/explore` + this file)
> Source: verified audit findings R-02 (CRITICAL), R-08 (HIGH), R-14 (MEDIUM), R-17 (MEDIUM) from `docs/AUDITORIA-FALLAS.md`.

## Scope

Fix the outbound communications domain (C-12). Architecture is sound (model → repository → service → worker; state machine, AES-256 on `destinatario`, approval gate at `get_todos_pendientes_elegibles` all correct). The 4 defects are localized and surgical.

## Current State (evidence)

### R-02 — Template rendering 100% broken (CRITICAL)
- `backend/app/services/comunicacion_service.py:37,93,99-111`.
- Documented public syntax is `{{alumno.nombre}}` / `{{alumno.email}}` (confirmed in `openspec/changes/archive/2026-06-10-c-12-comunicaciones-cola-worker/specs/comunicaciones-api/spec.md:6` and `tests/test_comunicaciones.py:191-192`).
- `_renderizar_plantilla()` converts `{{` → `${`, `}}` → `}`, producing `${alumno.nombre}`. `string.Template` only accepts `[_a-zA-Z][_a-zA-Z0-9]*` → dot keys raise `ValueError: Invalid placeholder` → caught and re-raised as HTTP 422.
- **Every** preview and batch-queue call with the documented syntax returns 422. `test_preview_renderiza_variables` (8.2) currently FAILS.
- **Zero migration**: templates are NOT persisted — `crear_lote` stores the already-rendered `asunto`/`cuerpo`. Substitution has been broken since day one, so no valid rendered data exists via this path.

### R-08 — Worker log flood (HIGH)
- `backend/app/workers/comunicacion_worker.py:59-66`. `run_once()` emits `logger.error` on every call when `webhook_url is None`. Loop interval 30s (`workers/main.py:49`) → ~2,880 ERROR/day. The `_WEBHOOK_NOT_CONFIGURED` sentinel (line 27) is unused; no "already warned" flag.

### R-14 — resetear_colgados on every cycle (MEDIUM)
- `backend/app/workers/comunicacion_worker.py:86`. Called unconditionally each `run_once()` → full-table `UPDATE ... WHERE estado='Enviando'` + COMMIT every 30s. Spec (`comunicaciones-worker/spec.md:33`) says "al arrancar el worker" (startup only).

### R-17 — get_pendientes_para_despacho missing aprobado filter (MEDIUM)
- `backend/app/repositories/comunicacion_repository.py:236-258`. Docstring promises `aprobado=True OR tenant sin aprobación`; the query has NO `aprobado` filter. Dead code today (worker uses `get_todos_pendientes_elegibles`, which filters correctly), but a trap for any future caller → would bypass the approval gate.

## Candidate Approaches

| Issue | Option | Pros | Cons |
|---|---|---|---|
| **R-02** | **A (rec)**: keep public `{{alumno.nombre}}`, normalize to `${alumno_nombre}` internally | Zero migration; preserves documented syntax; minimal diff | still on string.Template |
| R-02 | B: custom regex render for `{{dot.notation}}` | no internal conversion | custom engine = custom bugs |
| R-02 | C: Jinja2 sandboxed | feature-rich | new dep, overkill for 2 vars |
| **R-08** | **rec**: startup check in `_comunicacion_dispatch_loop` → one `logger.warning` + return; downgrade in-worker error to warning | clean separation | small `main.py` restructure |
| **R-14** | **rec**: `ComunicacionWorker.startup_run(db)` called once before the loop | explicit, testable | one extra session creation |
| **R-17** | **rec**: add `aprobado.is_(True)` to WHERE + fix docstring | one line | none |

## Affected Files & Blast Radius (~70 LOC)
- `backend/app/services/comunicacion_service.py` — `_renderizar_plantilla`, `_VARIABLES_DISPONIBLES` (R-02)
- `backend/app/workers/comunicacion_worker.py` — webhook check (R-08), extract `startup_run` (R-14)
- `backend/app/workers/main.py` — early return if no webhook (R-08), call `startup_run` before loop (R-14)
- `backend/app/repositories/comunicacion_repository.py` — `get_pendientes_para_despacho` filter (R-17)
- `backend/tests/test_comunicaciones.py` — fix tests 8.2–8.3 (failing today), add ~5 tests

## Test Strategy (real DB, no mocks; ephemeral pg on port 5433)
- Currently failing (R-02): `test_preview_renderiza_variables` (8.2) + triangulation.
- New: (1) `{{alumno.nombre}}` renders after fix; (2) unknown var → 422 with message; (3) `run_once` with `webhook_url=None` called N times logs once at WARNING (`caplog`); (4) `startup_run` calls `resetear_colgados`, later `run_once` calls do NOT; (5) `get_pendientes_para_despacho` excludes `aprobado=False`.

## Risks & Open Questions (for propose)
1. **Public syntax decision**: keep documented `{{alumno.nombre}}` (Approach A, no docs/UI change) vs migrate to `{{alumno_nombre}}` (touches docs + frontend). Recommendation: keep `{{alumno.nombre}}`.
2. **Frontend** `ComunicacionTracking.tsx` (329 LOC) may reference variable names — verify it needs no change if syntax stays.
3. **Startup session lifecycle** for `startup_run` — use the same `AsyncSessionLocal` pattern as the loop, once before `while True`.
4. No additional state-machine gaps found beyond the 4 issues.

## Hard Rules
PII AES-256 (unchanged), multi-tenancy (BaseRepository fail-closed, unchanged), approval gate (R-17 adds defense-in-depth), ≤500 LOC (all affected files under limit), no DB mocks.

## Next
`sdd-propose`.
