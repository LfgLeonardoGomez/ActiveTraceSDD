# Proposal: C-16 — Tareas Internas (Internal Task Workflow)

## Intent

Implement the internal task workflow for coordination ↔ teaching staff coordination (Épica 8, FL-05). Today there is no way for coordinators to assign, track, review, and close actionable tasks to docentes — forcing communication through informal channels. This change introduces the `Tarea` and `ComentarioTarea` models with a full state machine that reconciles E12 (data model) and FL-05 (user flow), covering task creation with closure criteria, docente progress reporting, and coordinator review/approval or return for rework.

## Scope

### In Scope
- `Tarea` model with extended fields: `criterio_cierre`, `revisada_por`, `revisada_at`, `devuelta`, `aprobada`
- `ComentarioTarea` model using `BaseModelMixin` (soft delete)
- 4-state enum: Pendiente → En progreso → Resuelta → Cancelada, plus `aprobada` flag
- CRUD endpoints under `/api/v1/tareas/*` with `tareas:gestionar` guard
- "My tasks" endpoint (F8.1), delegation (F8.2), admin view with filters (F8.3)
- State machine service enforcing valid transitions and approval/return logic
- Audit logging via `record_audit` helper
- Alembic migration `013_tareas_internas`
- Indexed queries for high-usage module (hundreds concurrent tasks)

### Out of Scope
- Frontend UI (deferred to C-21+)
- Notification/alert integration (separate change)
- Bulk task operations (batch assign, batch status change)
- Task templates or recurring task generation
- Dashboard/KPI metrics on tasks (later change)

## Capabilities

### New Capabilities
- `tareas-internas`: CRUD, state machine, delegation, filtering, and review/approval workflow for internal tasks between coordinators and docentes

### Modified Capabilities
- `audit-action-helper`: new audit action types for task lifecycle events (create, state change, approve, return, comment)

## Approach

Extend E12 with FL-05-reconciling fields. The `Tarea` model keeps the 4 states from E12 (Pendiente, En progreso, Resuelta, Cancelada) and adds an `aprobada: bool` flag to distinguish "Resolved by docente" from "Approved by coordinator". The service layer enforces the state machine: only the assignee advances state; only the assigner (or coordinator) approves or returns. `ComentarioTarea` uses `BaseModelMixin` for consistency with all other business entities. `contexto_id` remains an opaque UUID — no FK validation against specific tables. Indexes target tenant+estado, tenant+asignado_a+estado, and tenant+materia_id for the high-concurrency listing use case.

### Key Design Decisions

1. **E12 + FL-05 reconciliation** (pre-approved): Add `criterio_cierre`, `revisada_por`, `revisada_at`, `devuelta`, `aprobada` to `Tarea`.
2. **`aprobada` boolean** over a 5th state: Keeps the 4-state enum from E12 intact; `Resuelta + aprobada=True` means "closed by coordinator". Simpler for queries and filtering.
3. **`ComentarioTarea` with soft delete**: Same pattern as all other business entities via `BaseModelMixin`.
4. **`contexto_id` as opaque UUID**: No FK constraint — accepts any entity reference by design.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/tarea.py` | New | `Tarea` and `ComentarioTarea` models |
| `backend/app/schemas/tarea.py` | New | Request/response schemas with `extra='forbid'` |
| `backend/app/repositories/tarea_repository.py` | New | CRUD + tenant-scoped filtering |
| `backend/app/services/tarea_service.py` | New | State machine, delegation, approval logic |
| `backend/app/api/v1/routers/tareas.py` | New | REST endpoints |
| `backend/app/main.py` | Modified | Router registration |
| `backend/app/models/__init__.py` | Modified | Model exports |
| `backend/app/core/audit.py` | Modified | New audit action types for task events |
| `backend/alembic/versions/013_tareas_internas.py` | New | Schema migration |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Alembic head collision (two 011 migrations) | Medium | Resolve before C-16 migration; C-16 branches from resolved head |
| High concurrency on listing queries | High | Index on (tenant_id, estado), (tenant_id, asignado_a, estado), (tenant_id, materia_id); paginate all endpoints |
| `contexto_id` interpreted as FK by future devs | Low | Doc comment explicitly stating opaque reference, no FK constraint |
| FL-05/E12 divergence if KB is updated | Low | Proposal documents the reconciliation clearly; fields are additive |

## Rollback Plan

1. Remove router from `main.py`
2. Drop `013_tareas_internas` migration (or create `014_rollback_tareas` reverse migration)
3. Remove `tarea.py` model, repository, service, schemas, router files
4. Revert `audit.py` action type additions

## Dependencies

- C-07 (usuarios-y-asignaciones) — FK to `usuarios` for `asignado_a`, `asignado_por`, `revisada_por`
- C-04 (rbac-permisos-finos) — `tareas:gestionar` permission already seeded
- C-05 (audit-log) — `record_audit` helper pattern

## Success Criteria

- [ ] Coordinator can create a task with closure criteria and assign it to a docente
- [ ] Docente can view their assigned tasks, update state, and add comments
- [ ] Coordinator can approve (close) or return a resolved task with observation
- [ ] Admin view filters by docente, materia, estado, and free-text search
- [ ] All state transitions are audited; invalid transitions return 422
- [ ] Listing endpoints are indexed and paginated for concurrent use
- [ ] Tests cover ≥80% lines, ≥90% business rules (state machine, approval, return)