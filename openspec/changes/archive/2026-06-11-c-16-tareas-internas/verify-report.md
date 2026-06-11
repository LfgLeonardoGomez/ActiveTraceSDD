# Verification Report: C-16 — Tareas Internas

## Change Summary

| Field | Value |
|-------|-------|
| Change | C-16 tareas-internas |
| Mode | Standard verify + Strict TDD |
| Verdict | **FAIL** |
| Critical | 1 |
| Warning | 2 |
| Suggestion | 2 |

## Completeness

| Artifact | Status | Notes |
|----------|--------|-------|
| Proposal | ✅ Present | Full scope, risks, dependencies |
| Specs (tareas) | ✅ Present | 5 requirements, 12 scenarios |
| Specs (comentarios) | ✅ Present | 2 requirements, 4 scenarios |
| Design | ✅ Present | Data model, state machine, API contract, indexes |
| Tasks | ✅ Present | 17/17 tasks checked [x] |

## Task Completion

| Phase | Task | Status |
|-------|------|--------|
| 1 Foundation | 1.1 Migration 013_tareas_internas | ✅ Done |
| 1 Foundation | 1.2 Audit action types (9 TAREA_*) | ✅ Done |
| 2 Models | 2.1 Tarea, ComentarioTarea, EstadoTarea | ✅ Done |
| 2 Models | 2.2 Model exports | ✅ Done |
| 3 Schemas | 3.1 Pydantic schemas (10 schemas) | ✅ Done |
| 4 Repository | 4.1 TareaRepository | ✅ Done |
| 4 Repository | 4.2 ComentarioTareaRepository | ✅ Done |
| 5 Service | 5.1 State machine + approval | ✅ Done |
| 5 Service | 5.2 CRUD + delegation + comments | ✅ Done |
| 6 Router | 6.1 REST endpoints (12) | ✅ Done |
| 7 Wiring | 7.1 Register router | ✅ Done |
| 8 Testing | 8.1 Model + migration tests | ✅ Done |
| 8 Testing | 8.2 Schema validation tests | ✅ Done |
| 8 Testing | 8.3 Repository tests | ✅ Done |
| 8 Testing | 8.4 Service tests — state machine | ✅ Done |
| 8 Testing | 8.5 Router integration tests | ✅ Done |

**17/17 tasks complete.**

## Test Evidence

### Command
```
cd backend && .venv/bin/python -m pytest tests/test_tareas_*.py -v
```

### Result: 87 passed, 0 failed (32.89s)

| Test File | Tests | Status |
|-----------|-------|--------|
| test_tareas_models.py | 11 | ✅ All pass |
| test_tareas_schemas.py | 19 | ✅ All pass |
| test_tareas_repository.py | 17 | ✅ All pass |
| test_tareas_service.py | 26 | ✅ All pass |
| test_tareas_router.py | 14 | ✅ All pass |

### Mock check
No mocks detected. All DB tests use real DB via `db_session` fixture. ✅

### Coverage

| Module | Stmts | Miss | Cover | Missing Lines |
|--------|-------|------|-------|---------------|
| app/models/tarea.py | 34 | 0 | 100% | — |
| app/schemas/tarea.py | 75 | 0 | 100% | — |
| app/repositories/tarea_repository.py | 106 | 5 | 92% | 22, 127, 139, 152, 200 |
| app/services/tarea_service.py | 151 | 14 | 85% | 49, 130, 139, 222, 238, 260, 281, 291, 313, 323, 344, 368, 391, 411 |
| app/api/v1/routers/tareas.py | 73 | 2 | 95% | 63, 68 |
| **TOTAL** | **439** | **21** | **91%** | — |

- Lines coverage: **91%** ≥ 80% ✅
- Business rules coverage: state machine (all transitions ± invalid), approval, return, delegation, audit — **≥90%** ✅

## Spec Compliance Matrix

### tareas/spec.md

| Requirement | Scenario | Implementation | Test | Status |
|-------------|----------|----------------|------|--------|
| Task CRUD | Create task | `TareaService.crear()` → estado=Pendiente, aprobada=False | `test_crear_tarea` | ✅ PASS |
| Task CRUD | Update task | `TareaService.update_tarea()` | `test_update_tarea` | ✅ PASS |
| Task CRUD | Soft delete task | `TareaService.delete_tarea()` → soft_delete | `test_delete_tarea`, `test_soft_delete_tarea` | ✅ PASS |
| State Machine | Advance state (Pendiente→En progreso) | `_validar_transicion()` + assignee check | `test_pendiente_a_en_progreso` | ✅ PASS |
| State Machine | Resolve task (En progreso→Resuelta) | `_validar_transicion()` + assignee check | `test_en_progreso_a_resuelta` | ✅ PASS |
| State Machine | Approve task | `aprobar()` → aprobada=True, revisada_por/at | `test_aprobar_tarea` | ✅ PASS |
| State Machine | Return task | `devolver()` → devuelta=True, estado→En progreso | `test_resuelta_a_en_progreso_por_devolver` | ✅ PASS |
| State Machine | Invalid transition (422) | `_validar_transicion()` raises 422 | `test_invalid_transition_resuelta_a_en_progreso_directo`, `test_invalid_transition_pendiente_a_resuelta` | ✅ PASS |
| State Machine | Unauthorized state change (403) | `_validar_transicion()` raises 403 | `test_unauthorized_state_change` | ✅ PASS |
| Delegation | Delegate task | `delegar()` → reassigns asignado_a | `test_delegar_tarea` | ✅ PASS |
| Filtering | My tasks | `list_mis_tareas()` → filters by usuario_id | `test_mis_tareas`, `test_list_mis_tareas` | ✅ PASS |
| Filtering | Admin filtered view | `list_admin()` → estado, asignado_a, materia_id, search | `test_list_por_tenant_filter_*`, `test_list_tareas` | ✅ PASS |
| Audit | Audit creation | `record_audit(TAREA_CREAR)` | `test_crear_tarea` (audit check) | ✅ PASS |
| Audit | Audit approval | `record_audit(TAREA_APROBAR)` | `test_audit_aprobar` | ✅ PASS |

### comentarios/spec.md

| Requirement | Scenario | Implementation | Test | Status |
|-------------|----------|----------------|------|--------|
| Comment CRUD | Add comment | `TareaService.crear_comentario()` | `test_crear_comentario` (svc + router) | ✅ PASS |
| Comment CRUD | Soft delete comment | `TareaService.delete_comentario()` | `test_delete_comentario` (svc + repo) | ✅ PASS |
| Comment CRUD | **Unauthorized delete (403)** | **MISSING — no author/admin check** | **No test** | ❌ FAIL |
| Comment Listing | List comments (chronological) | `list_por_tarea()` → ORDER BY created_at ASC | `test_list_por_tarea_ordered`, `test_list_comentarios` | ✅ PASS |

## Design Coherence

| Design Decision | Implementation | Status |
|-----------------|----------------|--------|
| E12 + FL-05 reconciliation (additive fields) | criterio_cierre, aprobada, devuelta, revisada_por, revisada_at present | ✅ Aligned |
| `aprobada` boolean (not 5th state) | Boolean field, sets on approve | ✅ Aligned |
| `contexto_id` opaque UUID (no FK) | No ForeignKey in model or migration | ✅ Aligned |
| `ComentarioTarea` with BaseModelMixin (soft delete) | Inherits BaseModelMixin, deleted_at present | ✅ Aligned |
| 4 indexes | ix_tarea_tenant_estado, ix_tarea_asignado_estado, ix_tarea_materia, ix_comentario_tarea_tarea | ✅ Aligned |
| State machine transitions | Enforced in `_validar_transicion()`, aprobar(), devolver() | ✅ Aligned |
| 12 API endpoints | All present with correct methods and status codes | ✅ Aligned |
| 9 audit action types | All present in AuditAction enum | ✅ Aligned |
| Migration down_revision = "012_aviso_acknowledgment" | Confirmed | ✅ Aligned |

## Correctness Table

| Dimension | Check | Result |
|-----------|-------|--------|
| Model columns | All design columns present | ✅ |
| Model indexes | 3 composite + 1 single = 4 indexes | ✅ |
| Model FKs | asignado_a, asignado_por, revisada_por → usuarios; materia_id → materias; tarea_id → tarea | ✅ |
| Schema extra='forbid' | All 10 schemas have ConfigDict(extra="forbid") | ✅ |
| Repository tenant scoping | `_base_query()` filters tenant_id + deleted_at IS NULL | ✅ |
| Repository pagination | func.count + offset/limit on all list methods | ✅ |
| Service state machine | All valid/invalid transitions enforced | ✅ |
| Service audit | record_audit on create, update, delete, estado, aprobar, devolver, delegar, comentar, delete_comentario | ✅ |
| Router permission guard | `require_permission("tareas:gestionar")` on all 12 endpoints | ✅ |
| Router ordering | `/mis-tareas` before `/{tarea_id}` | ✅ |
| Migration down_revision | Points to "012_aviso_acknowledgment" | ✅ |
| Model exports | Tarea, ComentarioTarea, EstadoTarea in `__init__.py` + `__all__` | ✅ |
| Router registration | Imported and included in main.py | ✅ |

## Issues

### CRITICAL

| # | Issue | Spec Reference | Location | Detail |
|---|-------|----------------|----------|--------|
| C-1 | **Missing authorization check on `delete_comentario`** | comentarios/spec.md: "Unauthorized delete — GIVEN a comment by another user, WHEN a non-admin user tries to delete it, THEN the system returns 403" | `backend/app/services/tarea_service.py:408` | `delete_comentario()` soft-deletes any comment without checking if the caller is the comment author or an admin. Any user with `tareas:gestionar` permission can delete any comment. No test covers this scenario. |

### WARNING

| # | Issue | Location | Detail |
|---|-------|----------|--------|
| W-1 | **Missing `HTTPException` import in router** | `backend/app/api/v1/routers/tareas.py:23` | `_validate_page_size()` uses `HTTPException` and `status.HTTP_422_UNPROCESSABLE_ENTITY` but `HTTPException` is not imported. Will cause `NameError` at runtime when page_size > 100 or < 1. Not caught by tests because no test exercises those boundaries. |
| W-2 | **`update_tarea` can bypass delegation audit** | `backend/app/services/tarea_service.py` — `update_tarea()` | `TareaUpdateSchema` includes `asignado_a` field. PATCH `/{id}` can change the assignee without triggering `TAREA_DELEGAR` audit entry, bypassing the delegation trail. |

### SUGGESTION

| # | Issue | Location | Detail |
|---|-------|----------|--------|
| S-1 | **Deprecated `HTTP_422_UNPROCESSABLE_ENTITY`** | `tarea_service.py`, `test_tareas_service.py` | FastAPI deprecation warning: should use `HTTP_422_UNPROCESSABLE_CONTENT` instead. 4 occurrences in warnings. |
| S-2 | **Duplicate `EstadoTarea` enum** | `models/tarea.py` and `schemas/tarea.py` | Same enum defined in both files. Schema should import from model to avoid drift. |

## Final Verdict

### **FAIL**

**1 CRITICAL issue blocks archive readiness.**

The `delete_comentario` method in `TareaService` does not enforce the authorization check required by the comentarios spec: a non-admin user can delete another user's comment without receiving a 403. This is a missing spec requirement with no covering test.

Additionally, the router has a latent `NameError` bug (missing `HTTPException` import) that would crash on invalid page_size values.

### Required actions before archive:
1. **Fix C-1**: Add author/admin authorization check in `delete_comentario()` and add a test for the 403 scenario.
2. **Fix W-1**: Add `HTTPException` to the fastapi import in `tareas.py` router.
3. **Fix W-2** (recommended): Remove `asignado_a` from `TareaUpdateSchema` or add audit logging when it changes via update.
