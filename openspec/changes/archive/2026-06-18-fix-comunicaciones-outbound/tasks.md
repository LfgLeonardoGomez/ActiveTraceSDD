# Tasks: fix-comunicaciones-outbound

> Artifact store: hybrid · TDD: STRICT (pytest, real PG 5433, no DB mocks)
> Files touched: 5 · Spec requirements: R-02, R-08, R-14, R-17

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~130–160 (prod +37, tests +90) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | SIN PRs (no PR boundary required) |
| Chain strategy | N/A |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Notes |
|------|------|-------|
| 1 | R-17 repo filter + R-02 service normalization | Independent, both fail-safe fixes |
| 2 | R-08 log-flood gate + R-14 startup_run | Sequential within worker; R-08 gate first |
| 3 | All new tests + repair failing tests | Parallel with Unit 2 once Unit 1 done |

---

## Phase 1: RED — Write failing tests that evidence all 4 bugs

- [x] 1.1 `backend/tests/test_comunicaciones.py`: confirm `test_preview_renderiza_variables` (8.2) is RED — run `pytest -x -k test_preview_renderiza_variables` to document the current failure. **Req: R-02**
- [x] 1.2 Add `test_preview_dots_in_prose_preserved` — body `"Saludos. {{alumno.nombre}}. Atte."` → assert `"Saludos. Juan Pérez. Atte."` (prose dots untouched). Expect RED (normalization not yet applied). **Req: R-02**
- [x] 1.3 Add `test_preview_unknown_variable_422_shows_public_key` — body `"{{alumno.telefono}}"` → assert `HTTPException(status_code=422)` AND detail string contains `"alumno.telefono"` (public dot notation, not flat). Verify it fails RED if the 422 message currently prints the flat/raw `KeyError` key. **Req: R-02**
- [x] 1.4 Add `test_get_pendientes_para_despacho_excluye_no_aprobados` — insert two `Pendiente` rows (same tenant, one `aprobado=True`, one `aprobado=False`); call `ComunicacionRepository(db, tenant_id).get_pendientes_para_despacho(10)`; assert only the approved row is returned. Expect RED (filter missing). **Req: R-17**
- [x] 1.5 Add `test_get_pendientes_para_despacho_respeta_tenant` — two tenants, each with one approved `Pendiente`; call scoped to tenant A; assert only tenant A's row returned. (This may already pass; document status.) **Req: R-17**
- [x] 1.6 Add `test_dispatch_loop_no_webhook_logs_once_warning` — patch `Settings.n8n_webhook_url` to `None`; run `_comunicacion_dispatch_loop()` wrapped in `asyncio.wait_for(timeout=0.5)`; assert exactly ONE record in `caplog` at WARNING level containing `"dispatch_disabled"` and NO ERROR records, and that the coroutine completes without `TimeoutError`. Expect RED (currently loops + emits ERROR every cycle). **Req: R-08**
- [x] 1.7 Add `test_run_once_no_webhook_emits_warning_not_error` — instantiate `ComunicacionWorker(webhook_url=None, ...)`; call `run_once(db_session)` three times; assert all `caplog` records are WARNING, none are ERROR. Expect RED (currently emits ERROR). **Req: R-08**
- [x] 1.8 Add `test_startup_run_resets_stale_once_run_once_does_not` — seed a `Comunicacion` row stuck in `Enviando` with `updated_at` older than `stale_threshold_minutes` (real DB insert); call `worker.startup_run(db_session)` → assert return value `== 1` and row is now `Pendiente`; seed second stale row; call `worker.run_once(db_session)` twice → assert second row remains `Enviando`. Expect RED (`startup_run` not yet defined; `run_once` still resets). **Req: R-14**

---

## Phase 2: GREEN — Minimal implementation per fix (dependency order)

### 2a — R-17: repository filter (no other fix depends on this)

- [x] 2.1 `backend/app/repositories/comunicacion_repository.py` `get_pendientes_para_despacho` (L236-258): add `Comunicacion.aprobado.is_(True)` as the third predicate in the WHERE clause (copy from sibling `get_todos_pendientes_elegibles` L280). **Req: R-17**
- [x] 2.2 Same method: correct the docstring to state `Elegible = Pendiente + aprobado=True + no soft-deleted (scoped to current tenant)` — remove the incorrect "OR tenant no requiere aprobación" clause. **Req: R-17**
- [x] 2.3 Run `pytest -x -k "test_get_pendientes_para_despacho"` — both R-17 tests must go GREEN. **Req: R-17**

### 2b — R-02: template normalization (independent of 2a/2c/2d)

- [x] 2.4 `backend/app/services/comunicacion_service.py`: add module-level `_PLACEHOLDER = re.compile(r"\$\{([^}]*)\}")` and `def _normalize_key(public_key: str) -> str: return public_key.replace(".", "_")`. Import `re` at top if not present. **Req: R-02**
- [x] 2.5 Same file, `_renderizar_plantilla` (L~100): after the existing `{{`→`${` / `}}`→`}` conversion, add a second pass: `normalizada = _PLACEHOLDER.sub(lambda m: "${" + m.group(1).strip().replace(".", "_") + "}", normalizada)`. This scopes normalization to placeholder bodies only. **Req: R-02**
- [x] 2.6 Same file, `_renderizar_plantilla`: rewrite the value dict to use flat keys — `{_normalize_key("alumno.nombre"): nombre, _normalize_key("alumno.email"): email}`. **Req: R-02**
- [x] 2.7 Same file, `except KeyError as exc` block (L~112-120): replace raw `str(exc).strip("'")` with `flat = str(exc).strip("'"); publica = flat.replace("_", ".", 1)` and use `publica` in the 422 detail string. `_VARIABLES_DISPONIBLES` (L37) stays as-is (public dotted names). **Req: R-02**
- [x] 2.8 Run `pytest -x -k "test_preview_renderiza_variables or test_preview_dots_in_prose or test_preview_unknown_variable_422"` — all three R-02 tests must go GREEN. **Req: R-02**

### 2c — R-08: log-flood gate (must be done before 2d, which adds startup_run call in the same function)

- [x] 2.9 `backend/app/workers/main.py`, `_comunicacion_dispatch_loop` (L36): add the gate as the first statement after `settings = Settings()`: `if not settings.n8n_webhook_url: logger.warning("comunicacion_dispatch_disabled_no_webhook", extra={"event": "dispatch_disabled", "reason": "N8N_WEBHOOK_URL unset"}); return`. **Req: R-08**
- [x] 2.10 `backend/app/workers/comunicacion_worker.py`, `run_once` (L58-67): downgrade `logger.error` → `logger.warning` for the in-worker webhook-missing guard (defense-in-depth). Do not change the guard logic or `return` behavior. **Req: R-08**
- [x] 2.11 Run `pytest -x -k "test_dispatch_loop_no_webhook or test_run_once_no_webhook"` — both R-08 tests must go GREEN. **Req: R-08**

### 2d — R-14: startup_run lifecycle (depends on 2c gate being in place first)

- [x] 2.12 `backend/app/workers/comunicacion_worker.py`: add `async def startup_run(self, db_session: Any) -> int` method — guards `if not self.webhook_url: return 0`; constructs `_GlobalComunicacionRepository(db_session, _FAKE_TENANT)`; calls `await repo_global.resetear_colgados(self.stale_threshold_minutes)`; logs `info` if count > 0; returns count. Use `_FAKE_TENANT = UUID("00000000-0000-0000-0000-000000000001")`. **Req: R-14**
- [x] 2.13 Same file, `run_once` (L85-91): remove the `repo_global.resetear_colgados(...)` call block. Verify `repo_global` inside `run_once` is only used for `get_todos_pendientes_elegibles` + dispatch; if `_GlobalComunicacionRepository` is no longer needed in `run_once`, remove that instantiation too (check L82-94 scope). **Req: R-14**
- [x] 2.14 `backend/app/workers/main.py`, `_comunicacion_dispatch_loop`: after the R-08 gate (task 2.9) and before `while True`, add the `startup_run` call: `if AsyncSessionLocal is not None: startup_session = AsyncSessionLocal(); try: await worker.startup_run(startup_session); finally: await startup_session.close()`. **Req: R-14**
- [x] 2.15 Run `pytest -x -k "test_startup_run_resets_stale"` — R-14 test must go GREEN. **Req: R-14**

---

## Phase 3: Triangulation — verify edge cases and state-machine non-regression

- [x] 3.1 Add `test_preview_renderiza_multiples_destinatarios` is already present and GREEN — confirm it stays GREEN after R-02 changes (triangulation: per-alumno isolation). Run `pytest -k test_preview_renderiza_multiples_destinatarios`. **Req: R-02**
- [x] 3.2 Confirm `test_preview_no_persiste_nada` (8.4) still passes after R-02 changes — no `comunicacion` rows created. **Req: R-02, spec "Preview does not persist data"**
- [x] 3.3 Confirm `test_worker_N8N_exitoso` (8.17) passes — `Pendiente→Enviando→Enviado` transition unbroken after R-08/R-14 changes. **Req: R-08/R-14 non-regression, spec "Pendiente → Enviando → Enviado"**
- [x] 3.4 Confirm `test_worker_N8N_fallido` (8.18) passes — `Enviando→Error` transition unbroken. **Req: R-08/R-14 non-regression, spec "Enviando → Error on N8N failure"**
- [x] 3.5 Confirm `test_worker_sin_aprobacion_no_despacha` (8.19) passes — `run_once` still respects `aprobado` via `get_todos_pendientes_elegibles` (unchanged). **Req: R-17 non-regression**
- [x] 3.6 Confirm `test_worker_resetear_colgados` (8.20) passes — `resetear_colgados` still works via `startup_run` path. **Req: R-14 non-regression**
- [x] 3.7 Verify open design point: write a one-line comment in `startup_run` confirming "first `run_once` does NOT depend on a prior successful `startup_run`" (the existing `AsyncSessionLocal is None` guard in `run_once` at L54-57 handles not-ready state). **Req: R-14, design open point 3**

---

## Phase 4: Final verification run (comunicaciones scope only)

- [x] 4.1 Run `pytest backend/tests/test_comunicaciones.py -v --tb=short` — all tests in this file must pass. Record pass count (baseline + new tests). Do NOT run the full suite (95 other failing tests in unrelated domains). **All spec requirements** — RESULT: 45/45 passed
- [x] 4.2 Verify LOC on each modified production file stays under 500: `wc -l backend/app/services/comunicacion_service.py backend/app/workers/comunicacion_worker.py backend/app/workers/main.py backend/app/repositories/comunicacion_repository.py`. Expected: ~407, ~211, ~97, ~375. **Hard rule: ≤500 LOC/file** — RESULT: 417, 215, 103, 373 (all pass)
- [x] 4.3 Confirm `_VARIABLES_DISPONIBLES` is accessible from outside `_renderizar_plantilla` (it is already at module level L37 — verify no accidental scope change). **Req: R-02, design note on public 422 set** — CONFIRMED at L38
- [x] 4.4 Confirm `_WEBHOOK_NOT_CONFIGURED` sentinel (L27, `comunicacion_worker.py`) is left in place (no removal — out of scope per design open point 2). **Design constraint** — CONFIRMED at L27

---

## Spec → Task traceability

| Spec requirement | Satisfied by tasks |
|---|---|
| R-02: placeholder normalization (dot→underscore) | 1.1, 1.2, 2.4, 2.5, 2.6, 3.1 |
| R-02: unknown variable → 422 with public key | 1.3, 2.7, 2.8 |
| R-02: preview multi-recipient personalization | 3.1 |
| R-02: preview does not persist | 3.2 |
| R-08: single WARNING at loop startup, no loop entered | 1.6, 2.9, 2.11 |
| R-08: in-worker ERROR→WARNING downgrade | 1.7, 2.10, 2.11 |
| R-14: startup_run calls resetear_colgados once | 1.8, 2.12, 2.15, 3.6 |
| R-14: run_once does NOT call resetear_colgados | 1.8, 2.13, 2.15 |
| R-17: get_pendientes_para_despacho aprobado filter | 1.4, 2.1, 2.3 |
| R-17: tenant isolation unchanged | 1.5, 2.2, 2.3 |
| State machine non-regression | 3.3, 3.4, 3.5 |
