# Verification Report: fix-comunicaciones-outbound

> Phase: SDD verify · Artifact store: hybrid · TDD: STRICT (pytest, real PG 5433, no DB mocks)
> Verdict: **PASS** · Date: 2026-06-18

## Test Execution Evidence (REAL)

Command:
```
cd backend && DATABASE_URL=postgresql+asyncpg://trace_user:trace_pass@localhost:5433/activia_trace \
  .venv/bin/python -m pytest tests/test_comunicaciones.py -q
```
Result: **45 passed, 0 failed, 8 warnings in 29.09s**

Warnings are pre-existing `HTTP_422_UNPROCESSABLE_ENTITY` deprecation notices (Starlette) and a passlib `crypt` deprecation — neither introduced by this change, both non-blocking.

## Task Completeness

28/28 tasks marked `[x]`. Spot-checked all four requirement fixes in source — all genuinely implemented (not checkbox-only):

| Req | File | Evidence |
|-----|------|----------|
| R-02 | `app/services/comunicacion_service.py` | `_PLACEHOLDER` regex (L41), `_normalize_key` (L44), body-scoped `.sub` (L118-119), flat value dict (L125-126), cosmetic un-flatten in 422 (L134-136), `_VARIABLES_DISPONIBLES` keeps public dot syntax (L38) |
| R-08 | `app/workers/main.py` + `comunicacion_worker.py` | Startup gate: single `logger.warning("comunicacion_dispatch_disabled")` + `return` before loop; in-worker guard downgraded to `logger.warning` |
| R-14 | `app/workers/comunicacion_worker.py` | `startup_run` (def @1753) is the ONLY caller of `resetear_colgados` (@2634, inside startup_run, before run_once @2942); `run_once` no longer resets; lifecycle comment present (task 3.7) |
| R-17 | `app/repositories/comunicacion_repository.py` | `Comunicacion.aprobado.is_(True)` predicate added + tenant scope intact + corrected docstring |

## Spec Compliance Matrix (scenario → test → result)

### comunicaciones-api
| Spec scenario | Covering test | Result |
|---|---|---|
| Preview renders documented dot-notation variables | `test_preview_renderiza_variables` | PASS |
| Preview multi-recipient personalization | `test_preview_renderiza_multiples_destinatarios` | PASS |
| Preview unknown variable → 422 with public key | `test_preview_unknown_variable_422_shows_public_key` | PASS |
| Preview does not persist | `test_preview_no_persiste` | PASS |
| Variable inválida (existing) | `test_preview_variable_invalida_422`, `test_preview_variable_invalida_en_cuerpo_422` | PASS |
| Literal dots in prose preserved (triangulation) | `test_preview_dots_in_prose_preserved` | PASS |
| get_pendientes_para_despacho excludes unapproved | `test_get_pendientes_para_despacho_excluye_no_aprobados` | PASS |
| get_pendientes_para_despacho tenant isolation | `test_get_pendientes_para_despacho_respeta_tenant` | PASS |

### comunicaciones-worker
| Spec scenario | Covering test | Result |
|---|---|---|
| Dispatch loop no webhook — single WARNING, no loop entered | `test_dispatch_loop_no_webhook_logs_once_warning` | PASS |
| Dispatch loop webhook set — normal operation | (covered by `test_worker_despacha_exitosamente` path) | PASS |
| run_once no webhook — WARNING not ERROR | `test_run_once_no_webhook_emits_warning_not_error` | PASS |
| startup_run resets stale once; run_once does NOT | `test_startup_run_resets_stale_once_run_once_does_not` | PASS |
| Stale Enviando reset at startup (unchanged) | `test_resetear_colgados_transiciona_a_pendiente` | PASS |
| Recent Enviando not touched (unchanged) | `test_resetear_colgados_no_toca_recientes` | PASS |
| State machine Pendiente→Enviando→Enviado | `test_worker_despacha_exitosamente` | PASS |
| State machine Enviando→Error on N8N failure | `test_worker_n8n_fallido_marca_error`, `test_worker_n8n_timeout_marca_error` | PASS |
| Unapproved not dispatched (R-17 non-regression) | `test_worker_no_despacha_sin_aprobacion` | PASS |

All 11 target scenarios covered by a test that passed at runtime.

## Hard Rules Compliance

| Hard rule | Status |
|---|---|
| PII destinatario AES-256 untouched | PASS — `test_worker_descifra_destinatario_correctamente` green; no crypto code touched |
| Multi-tenancy row-level in repo | PASS — `get_pendientes_para_despacho` keeps `tenant_id` predicate; `aprobado` is an added AND; `test_get_pendientes_para_despacho_respeta_tenant` green |
| Approval gate before dispatch (R-17 reinforces) | PASS — defense-in-depth filter added; live path (`get_todos_pendientes_elegibles`) unchanged |
| Tests without DB mocks | PASS — only N8N HTTP client and Settings are mocked; DB is real PG 5433 |
| ≤500 LOC per backend file | PASS — service 417, worker 215, main 103, repo 373 |
| `_WEBHOOK_NOT_CONFIGURED` sentinel left in place | PASS — present (out-of-scope per design open point 2) |

## Issues

### CRITICAL
None.

### WARNING
None.

### SUGGESTION
1. The tasks.md trace table references some non-regression tests by aspirational names
   (`test_worker_N8N_exitoso`, `test_worker_sin_aprobacion_no_despacha`,
   `test_worker_resetear_colgados`). The actual test names in the file differ
   (`test_worker_despacha_exitosamente`, `test_worker_no_despacha_sin_aprobacion`,
   `test_resetear_colgados_transiciona_a_pendiente`). The coverage is equivalent and all pass;
   this is a naming-reference mismatch in the tasks doc, not a coverage gap.
2. Pre-existing `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warnings could be migrated to
   `HTTP_422_UNPROCESSABLE_CONTENT` in a future cleanup — out of scope here.
3. No engram artifacts exist for this change (spec/tasks/design/apply-progress live only in
   openspec files). Hybrid mode expected both; the engram side was never written by the
   upstream phases. Not blocking; flagged for pipeline hygiene.

## Verdict

**PASS** — All 28 tasks implemented and verified in source. All 11 target spec scenarios
covered by tests that passed at runtime (45/45 green). R-02, R-08, R-14, R-17 each fully
resolved (not partial). Public `{{alumno.nombre}}` syntax preserved. No hard-rule regressions.

Next recommended: **sdd-archive**.
