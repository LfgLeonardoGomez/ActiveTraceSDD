# Tasks: C-16 — Tareas Internas

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1050 (code ~550 + tests ~500) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | Single PR (per delivery strategy) — see risks |
| Delivery strategy | single-pr |
| Chain strategy | N/A (single PR) |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: N/A
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Full module (foundation → wiring → tests) | PR 1 | Single PR per delivery strategy; ~1050 lines exceeds 800-line budget — flag for maintainer |

## Phase 1: Foundation

- [x] 1.1 **Migration `013_tareas_internas`** — Create `backend/alembic/versions/013_tareas_internas.py`. Tables: `tarea` (titulo, descripcion, criterio_cierre, estado, aprobada, devuelta, asignado_a, asignado_por, revisada_por, revisada_at, materia_id, contexto_id + BaseModelMixin columns) and `comentario_tarea` (tarea_id, autor_id, contenido + BaseModelMixin columns). FKs to usuarios, materias, tarea. Indexes: `ix_tarea_tenant_estado`, `ix_tarea_asignado_estado`, `ix_tarea_materia`, `ix_comentario_tarea_tarea`. `down_revision = "012_aviso_acknowledgment"`.
  - Files: `backend/alembic/versions/013_tareas_internas.py`
  - Dependencies: none
  - Est: ~80 lines

- [x] 1.2 **Audit action types** — Add 9 `TAREA_*` entries to `AuditAction` enum in `backend/app/core/audit.py`: `TAREA_CREAR`, `TAREA_ACTUALIZAR`, `TAREA_ELIMINAR`, `TAREA_ESTADO_CAMBIAR`, `TAREA_APROBAR`, `TAREA_DEVOLVER`, `TAREA_DELEGAR`, `TAREA_COMENTAR`, `TAREA_COMENTARIO_ELIMINAR`.
  - Files: `backend/app/core/audit.py`
  - Dependencies: none
  - Est: ~9 lines

## Phase 2: Models

- [x] 2.1 **Tarea, ComentarioTarea, EstadoTarea** — Create `backend/app/models/tarea.py`. `EstadoTarea(StrEnum)` with Pendiente/En progreso/Resuelta/Cancelada. `Tarea(BaseModelMixin, Base)` with all design columns + 3 composite indexes. `ComentarioTarea(BaseModelMixin, Base)` with tarea_id FK CASCADE, autor_id FK RESTRICT, contenido Text. Follow `aviso.py` pattern exactly.
  - Files: `backend/app/models/tarea.py`
  - Dependencies: 1.1
  - Est: ~55 lines

- [x] 2.2 **Model exports** — Add `Tarea`, `ComentarioTarea`, `EstadoTarea` to `backend/app/models/__init__.py` imports and `__all__`.
  - Files: `backend/app/models/__init__.py`
  - Dependencies: 2.1
  - Est: ~5 lines

## Phase 3: Schemas

- [x] 3.1 **Pydantic schemas** — Create `backend/app/schemas/tarea.py` with `extra='forbid'` on all. Create: `TareaCreateSchema` (titulo, descripcion?, criterio_cierre?, asignado_a, materia_id?, contexto_id?), `TareaUpdateSchema` (all optional), `TareaResponseSchema` (full model fields), `TareaListResponseSchema` (items+total+page+pages), `TareaEstadoSchema` (estado: EstadoTarea), `DevolverTareaSchema` (observacion: str), `DelegarTareaSchema` (nuevo_asignado_id: UUID), `ComentarioCreateSchema` (contenido), `ComentarioResponseSchema` (id, tarea_id, autor_id, contenido, timestamps), `ComentarioListResponseSchema`.
  - Files: `backend/app/schemas/tarea.py`
  - Dependencies: 2.1
  - Est: ~110 lines

## Phase 4: Repository

- [x] 4.1 **TareaRepository** — Create `backend/app/repositories/tarea_repository.py`. Constructor takes `(db_session, tenant_id)`. Methods: `create(data)`, `get_by_id(tarea_id)`, `list_por_tenant(page, page_size, estado?, asignado_a?, materia_id?, search?)` with `func.count` + offset pagination, `list_por_asignado(asignado_a, page, page_size, estado?)`, `update(tarea_id, data)`, `soft_delete(tarea_id)`. All queries filter `tenant_id` + `deleted_at IS NULL`. Follow `aviso_repository.py` pattern.
  - Files: `backend/app/repositories/tarea_repository.py`
  - Dependencies: 2.1
  - Est: ~120 lines

- [x] 4.2 **ComentarioTareaRepository** — Create in same file or separate. Methods: `create(data)`, `list_por_tarea(tarea_id, page, page_size)` ordered by `created_at ASC`, `soft_delete(comentario_id)`. All filter by tenant_id + deleted_at IS NULL.
  - Files: `backend/app/repositories/tarea_repository.py` (append)
  - Dependencies: 2.1
  - Est: ~50 lines

## Phase 5: Service

- [x] 5.1 **TareaService — state machine + approval** — Create `backend/app/services/tarea_service.py`. Constructor: `(db_session, tenant_id, usuario_id)`. Implement `_validar_transicion(origen, destino, actor_id, tarea)` enforcing: Pendiente→En progreso (assignee), En progreso→Resuelta (assignee), En progreso→Cancelada (assignee/assigner), Any→Cancelada. `aprobar()`: only Resuelta, sets `aprobada=True`, `revisada_por`, `revisada_at`. `devolver(observacion)`: only Resuelta, sets `devuelta=True`, estado→En progreso. Both raise `HTTPException(422)` on invalid state. Follow `aviso_service.py` pattern.
  - Files: `backend/app/services/tarea_service.py`
  - Dependencies: 3.1, 4.1
  - Est: ~100 lines

- [x] 5.2 **TareaService — CRUD + delegation + comments** — Add to same file: `crear(data)` → audit TAREA_CREAR, `get_tarea(id)`, `list_admin(filtros, page, page_size)`, `list_mis_tareas(page, page_size, estado?)`, `update_tarea(id, data)` → audit TAREA_ACTUALIZAR, `delete_tarea(id)` → audit TAREA_ELIMINAR, `cambiar_estado(id, nuevo_estado, actor_id)` → audit TAREA_ESTADO_CAMBIAR, `delegar(id, nuevo_asignado_id)` → audit TAREA_DELEGAR, `crear_comentario(tarea_id, data)` → audit TAREA_COMENTAR, `list_comentarios(tarea_id, page, page_size)`, `delete_comentario(comentario_id)` → audit TAREA_COMENTARIO_ELIMINAR.
  - Files: `backend/app/services/tarea_service.py` (append)
  - Dependencies: 5.1, 4.2
  - Est: ~100 lines

## Phase 6: Router

- [x] 6.1 **REST endpoints** — Create `backend/app/api/v1/routers/tareas.py`. Prefix `/api/tareas`. All endpoints guard `require_permission("tareas:gestionar")`. Endpoints: `POST /` (201), `GET /` (admin list with query filters), `GET /mis-tareas`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`, `PATCH /{id}/estado`, `POST /{id}/aprobar`, `POST /{id}/devolver`, `POST /{id}/delegar`, `POST /{id}/comentarios` (201), `GET /{id}/comentarios`. Use `_make_service()` helper + `_validate_page_size()` from avisos pattern.
  - Files: `backend/app/api/v1/routers/tareas.py`
  - Dependencies: 5.2
  - Est: ~200 lines

## Phase 7: Wiring

- [x] 7.1 **Register router** — Add `from app.api.v1.routers.tareas import router as tareas_router` and `app.include_router(tareas_router)` to `backend/app/main.py`.
  - Files: `backend/app/main.py`
  - Dependencies: 6.1
  - Est: ~3 lines

## Phase 8: Testing (Strict TDD)

- [x] 8.1 **Model + migration tests** — Create `backend/tests/test_tareas_models.py`. Test: EstadoTarea enum values, Tarea creation with defaults (estado=Pendiente, aprobada=False, devuelta=False), ComentarioTarea FK constraints, soft delete sets deleted_at, indexes exist.
  - Files: `backend/tests/test_tareas_models.py`
  - Dependencies: 2.1, 1.1
  - Est: ~60 lines

- [x] 8.2 **Schema validation tests** — Create `backend/tests/test_tareas_schemas.py`. Test: `extra='forbid'` rejects unknown fields, required fields enforced, EstadoTarea values accepted, UUID fields validated, pagination schema defaults.
  - Files: `backend/tests/test_tareas_schemas.py`
  - Dependencies: 3.1
  - Est: ~50 lines

- [x] 8.3 **Repository tests** — Create `backend/tests/test_tareas_repository.py`. Use real DB (no mocks). Test: CRUD operations, tenant isolation (other tenant can't see), list filters (estado, asignado_a, materia_id, search), pagination, soft delete excludes from listings, comentario list ordered ASC.
  - Files: `backend/tests/test_tareas_repository.py`
  - Dependencies: 4.1, 4.2
  - Est: ~150 lines

- [x] 8.4 **Service tests — state machine** — Create `backend/tests/test_tareas_service.py`. Test ALL transitions: valid (Pendiente→En progreso, En progreso→Resuelta, approve, return→En progreso, cancel) and invalid (Resuelta→En progreso without return, Pendiente→Resuelta, approve non-Resuelta=422, return non-Resuelta=422). Test unauthorized state change=403. Test delegation reassigns asignado_a. Test audit entries created for each action.
  - Files: `backend/tests/test_tareas_service.py`
  - Dependencies: 5.1, 5.2
  - Est: ~180 lines

- [x] 8.5 **Router integration tests** — Create `backend/tests/test_tareas_router.py`. Test each endpoint returns correct status (201/200/404/403/422), permission guard `tareas:gestionar`, mis-tareas returns only assigned, admin filters work, comentarios CRUD, pagination params. Use TestClient with auth override.
  - Files: `backend/tests/test_tareas_router.py`
  - Dependencies: 6.1, 7.1
  - Est: ~200 lines
