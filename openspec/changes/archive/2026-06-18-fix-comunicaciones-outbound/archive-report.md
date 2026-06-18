# Archive Report: fix-comunicaciones-outbound

> Archived: 2026-06-18 · Artifact store: hybrid · SDD cycle: complete

## Intent

Restore the outbound communications flow broken since C-12 implementation: template preview
returned HTTP 422 for every documented variable (R-02, CRITICAL), the dispatch worker
emitted ~2,880 ERROR/day when N8N was unconfigured (R-08, HIGH), `resetear_colgados` ran
on every 30s cycle instead of once at startup (R-14, MEDIUM), and
`get_pendientes_para_despacho` lacked the required `aprobado` filter (R-17, MEDIUM,
defense-in-depth).

## Outcome

**PASS — 45/45 tests green, 0 CRITICAL, 0 WARNING issues at verify.**

All four defects resolved:

| Fix | Requirement | Status |
|-----|-------------|--------|
| Template normalization: dot→underscore scoped to placeholder bodies | R-02 | Resolved |
| Dispatch loop startup gate: single WARNING + return when N8N unset | R-08 | Resolved |
| `startup_run` method: `resetear_colgados` runs once per process, not per cycle | R-14 | Resolved |
| `aprobado.is_(True)` predicate added to `get_pendientes_para_despacho` | R-17 | Resolved |

## Code Modified

| File | Change summary |
|------|----------------|
| `backend/app/services/comunicacion_service.py` | Added `_PLACEHOLDER` regex + `_normalize_key`; rewrote `_renderizar_plantilla` placeholder normalization; flat value dict; display-only un-flatten in 422 message. Final LOC: 417. |
| `backend/app/workers/main.py` | Startup webhook gate (single WARNING + return before `while True`); `startup_run` call before loop. Final LOC: 103. |
| `backend/app/workers/comunicacion_worker.py` | Added `startup_run(db)` method; removed `resetear_colgados` from `run_once`; downgraded in-worker logger.error → logger.warning. Final LOC: 215. |
| `backend/app/repositories/comunicacion_repository.py` | Added `Comunicacion.aprobado.is_(True)` predicate; corrected docstring. Final LOC: 373. |
| `backend/tests/test_comunicaciones.py` | Repaired 2 previously failing tests; added 8 new tests covering R-02/R-08/R-14/R-17 scenarios. |

## Specs Merged into Canonical Source of Truth

| Domain | Action | Requirements merged |
|--------|--------|--------------------|
| `comunicaciones-api` | MODIFIED + ADDED | MODIFIED: "Preview de mensaje antes de encolar" (added normalization contract, expanded scenarios); ADDED: "Approval filter on get_pendientes_para_despacho" (new requirement) |
| `comunicaciones-worker` | MODIFIED x2 | MODIFIED: "N8N_WEBHOOK_URL no configurado" (startup gate, single WARNING, no ERROR); MODIFIED: "Reseteo de mensajes colgados al iniciar el worker" (startup_run contract, run_once exclusion) |

Canonical specs updated:
- `openspec/specs/comunicaciones-api/spec.md`
- `openspec/specs/comunicaciones-worker/spec.md`

## Deferred Technical Debt

1. **`_WEBHOOK_NOT_CONFIGURED` sentinel** (`comunicacion_worker.py` L27): defined but unused.
   Left in place per design open point 2 (trivial cleanup, out of scope for this change).
2. **`HTTP_422_UNPROCESSABLE_ENTITY` deprecation**: Starlette 1.3 deprecates this constant
   in favor of `HTTP_422_UNPROCESSABLE_CONTENT`. Pre-existing across the codebase; 8 warnings
   at test time. Not blocking, but should be migrated in a future chore change.
3. **Engram artifacts missing for upstream phases**: hybrid mode expected spec/design/tasks to
   be saved to engram; the engram side was never written by those phases. openspec files were
   the authoritative source throughout. Pipeline hygiene issue for future changes.

## SDD Cycle Summary

| Phase | Status |
|-------|--------|
| explore | Done |
| propose | Done |
| spec | Done |
| design | Done |
| tasks | Done (28/28 tasks [x]) |
| apply | Done |
| verify | PASS (45/45 green, 0 CRITICAL/WARNING) |
| archive | Done — 2026-06-18 |

## Artifact Trail (openspec)

All change artifacts archived at:
`openspec/changes/archive/2026-06-18-fix-comunicaciones-outbound/`

- `exploration.md`
- `proposal.md`
- `design.md`
- `tasks.md`
- `verify-report.md`
- `specs/comunicaciones-api/spec.md` (delta — preserved for audit trail)
- `specs/comunicaciones-worker/spec.md` (delta — preserved for audit trail)
- `archive-report.md` (this file)
