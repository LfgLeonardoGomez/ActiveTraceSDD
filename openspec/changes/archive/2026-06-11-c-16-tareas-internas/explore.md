## Exploration: C-16 tareas-internas

### Current State

The backend already has a solid foundation for C-16:
- **Permission `tareas:gestionar`** exists and is seeded in migration `002_create_rbac_tables.py` (assigned to COORDINADOR and ADMIN roles).
- **Audit helpers** (`record_audit`, `AuditAction`) are available in `app.core.audit` and used by `AvisoService`.
- **BaseModelMixin** is the standard for all business entities (UUID id, tenant_id, created_at, updated_at, deleted_at).
- **BaseRepository** provides generic CRUD with tenant scoping and soft-delete.
- **Router pattern** uses `require_permission("modulo:accion")`, `CurrentUser`, `get_db`.
- **Latest migrations** are `011_avisos.py` and `011_aviso_acknowledgment.py` (both branch from `010_evaluaciones`). The next migration for C-16 will be `012_tareas_internas.py`.

### Affected Areas

- `backend/app/models/tarea.py` — new models `Tarea` + `ComentarioTarea`
- `backend/app/schemas/tarea.py` — request/response schemas with `extra='forbid'`
- `backend/app/repositories/tarea_repository.py` — CRUD + filtering by tenant + estado
- `backend/app/services/tarea_service.py` — state machine, delegation logic, audit logging
- `backend/app/api/v1/routers/tareas.py` — endpoints under `/api/tareas/*`
- `backend/app/main.py` — router registration
- `backend/app/models/__init__.py` — exports
- `backend/alembic/versions/012_tareas_internas.py` — schema migration

### Approaches

1. **Strict E12 implementation** — Build exactly what the KB data model says (Tarea + ComentarioTarea with 4 states).
   - Pros: Simple, matches the spec exactly.
   - Cons: FL-05 mentions "criterio de cierre", "aprobar cierre", "devolver al docente" — these have NO representation in E12. The feature would be incomplete.
   - Effort: Low

2. **E12 + FL-05 reconciliation** — Extend E12 to cover the FL-05 workflow: add `criterio_cierre`, `revisada_por`, `revisada_at`, `devuelta` fields, and a 5th state (or keep 4 states + flags).
   - Pros: Covers the full workflow described in the user-facing flow. Future-proof for high-usage module.
   - Cons: Diverges slightly from the KB E12 text. Requires a design decision in the proposal phase.
   - Effort: Medium

3. **E12 with state machine in service** — Keep the DB schema minimal (E12) but encode the FL-05 logic (approval/return) entirely in the service layer via state transitions + comments.
   - Pros: Minimal schema change.
   - Cons: "Criterio de cierre" is a structured field, not a comment. Storing it in a comment is a hack. Also, "devolver al docente" is an explicit action that should be auditable.
   - Effort: Medium

### Recommendation

**Approach 2 (E12 + FL-05 reconciliation)**.

The FL-05 flow is explicit and the module is marked as high-usage. The schema should reflect the workflow:
- Add `criterio_cierre: text | None` (closure criteria set by the assigner).
- Add `revisada_por: UUID | None` (FK to usuarios) and `revisada_at: datetime | None` (who approved the closure).
- Add `devuelta: bool` default=False (or an extra state `Devuelta`).
- Keep the 4 states from E12 but add a flag `cerrada` or `aprobada` to distinguish between "Resuelta" (docente says it's done) and "Cerrada" (coordinator approved).

**Index strategy** for high usage:
- `ix_tarea_tenant_estado` (tenant_id, estado) — listing by state
- `ix_tarea_asignado_a` (tenant_id, asignado_a, estado) — "my tasks" view
- `ix_tarea_materia` (tenant_id, materia_id) — filtering by materia
- `ix_comentario_tarea_tarea` (tarea_id) — comments by task

### Risks

1. **FL-05 discrepancy**: The KB data model (E12) and the main flow (FL-05) are NOT aligned. The proposal must decide whether to add schema fields or keep the logic in the service layer.
2. **Alembic head collision**: There are already two `011` migrations (`011_avisos` and `011_aviso_acknowledgment`). Before creating `012`, the migration chain must be resolved (merge or one of them must be renamed). This is a project-wide risk, not specific to C-16.
3. **High usage**: The CHANGES.md notes "cientos de tareas en simultáneo". Listing endpoints must be indexed and paginated. Avoid N+1 when loading comments.
4. **Contexto_id**: It is an opaque UUID reference. The service should accept it as optional and never validate it against a specific table (by design, it is polymorphic).
5. **ComentarioTarea soft delete**: The KB does not explicitly show `deleted_at` for `ComentarioTarea`, but every other business entity in the codebase uses `BaseModelMixin`. Deviating from the pattern requires a conscious decision.

### Ready for Proposal

**Yes**, with the following clarifications needed:

1. **Should the proposal extend E12 to include `criterio_cierre`, `revisada_por`, `revisada_at`, and `devuelta`?** (FL-05 vs E12 gap)
2. **Should ComentarioTarea have soft delete (BaseModelMixin) or be a pure relation table (no soft delete)?**
3. **Should the Alembic head collision be resolved before or during the C-16 proposal?**

The orchestrator should present these 3 questions to the user (or decide if the project convention is to always reconcile KB and flows). Once clarified, the next phase is `sdd-propose`.
