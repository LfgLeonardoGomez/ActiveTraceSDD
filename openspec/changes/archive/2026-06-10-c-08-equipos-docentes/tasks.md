# Tasks: C-08 Equipos Docentes

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~720 (5 new files ~670 + 3 modified files ~50) |
| 800-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | N/A |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: N/A
400-line budget risk: Low

## Phase 1: Foundation (Schemas + Dependencies)

- [x] 1.1 Add `openpyxl` to `backend/pyproject.toml` dependencies list
- [x] 1.2 Create `backend/app/schemas/equipos.py` with all Pydantic schemas (`extra="forbid"` on all):
  - `EquipoRead` — full assignment row + denormalized `materia_nombre`, `carrera_nombre`, `cohorte_nombre`, `usuario_nombre`, `usuario_apellidos` + computed `estado_vigencia`
  - `EquipoFilterParams` — optional `materia_id`, `carrera_id`, `cohorte_id`, `estado_vigencia`
  - `PaginatedEquipoResponse` — `items: list[EquipoRead]`, `total`, `limit`, `offset`
  - `AsignacionMasivaRequest` — `usuario_ids: list[UUID]` (min_length=1, max_length=100), `materia_id`, `carrera_id`, `cohorte_id`, `rol`, `desde`, `hasta`
  - `AsignacionMasivaResponse` — `count: int`, `created_ids: list[UUID]`
  - `ClonarEquipoRequest` — `materia_id`, `carrera_id`, `cohorte_id_origen`, `cohorte_id_destino`, `desde`, `hasta`, `preview: bool = False`
  - `ClonarEquipoResponse` — `preview_count`, `created_count | None`, `created_ids | None`
  - `ActualizarVigenciaRequest` — `materia_id`, `carrera_id`, `cohorte_id`, `desde`, `hasta`
  - `ActualizarVigenciaResponse` — `count: int`
  - `ExportarEquipoParams` — query params: `materia_id`, `carrera_id`, `cohorte_id`, `format` (csv|xlsx), `include_pii` (bool)

## Phase 2: Repository Layer

- [x] 2.1 Create `backend/app/repositories/equipos.py` with `EquipoRepository` class (takes `AsyncSession` + `tenant_id`):
  - `list_by_equipo(materia_id, carrera_id, cohorte_id, estado_vigencia?, limit, offset)` → JOIN Asignacion ↔ Usuario ↔ Materia ↔ Carrera ↔ Cohorte, return enriched rows + total count. Filter `deleted_at IS NULL` on all joined tables.
  - `list_by_usuario(usuario_id, filters?, limit, offset)` → same JOIN pattern, filtered by `usuario_id`, for mis-equipos
  - `bulk_create_assignments(items: list[dict])` → `db.add_all([Asignacion(**item, tenant_id=self.tenant_id) for item in items])`, then `await db.flush()` (no commit — caller commits)
  - `clone_vigentes(materia_id, carrera_id, cohorte_id_origen, cohorte_id_destino, desde, hasta)` → SELECT vigentes (desde ≤ today AND (hasta IS NULL OR hasta ≥ today)), INSERT copies with new cohorte_id + new dates, `flush()`. Return list of created instances.
  - `update_vigencia_by_equipo(materia_id, carrera_id, cohorte_id, desde, hasta)` → UPDATE all vigentes matching equipo key with new dates, `flush()`. Return count.
  - `get_equipo_for_export(materia_id, carrera_id, cohorte_id, include_pii)` → full JOIN query returning enriched rows for export (include/exclude PII columns based on flag)

## Phase 3: Service Layer

- [x] 3.1 Create `backend/app/services/equipos.py` with `EquipoService` class:
  - Constructor: takes `db: AsyncSession`, `tenant_id: UUID`. Instantiates `EquipoRepository`, `AsignacionRepository`, `UsuarioRepository`, `AuditLogRepository`.
  - `mis_equipos(current_user, filters: EquipoFilterParams, limit, offset)` → delegates to `_repo_equipo.list_by_usuario(current_user.id, ...)`, maps to `EquipoRead` list + total
  - `list_equipo(materia_id, carrera_id, cohorte_id, estado_vigencia?, limit, offset)` → delegates to `_repo_equipo.list_by_equipo(...)`, maps to `PaginatedEquipoResponse`
  - `asignacion_masiva(data: AsignacionMasivaRequest, current_user)` → (1) validate all `usuario_ids` exist via `UsuarioRepository.get_by_id` — if any missing, raise 422 with specific uuid; (2) call `_repo_equipo.bulk_create_assignments(...)`; (3) `await db.commit()`; (4) insert `AuditLog(accion="ASIGNACION_CREAR", filas_afectadas=count, detalle={team_key})`; (5) `await db.commit()`; (6) return `AsignacionMasivaResponse`
  - `clonar_equipo(data: ClonarEquipoRequest, current_user)` → if `preview=True`: count vigentes via repo query, return `ClonarEquipoResponse(preview_count=N)`. If `preview=False`: call `_repo_equipo.clone_vigentes(...)`, commit, audit log `ASIGNACION_CLONAR`, return response with `created_count` + `created_ids`
  - `actualizar_vigencia(data: ActualizarVigenciaRequest, current_user)` → call `_repo_equipo.update_vigencia_by_equipo(...)`. If count=0, raise 422 "No hay asignaciones vigentes en el equipo". Commit, audit log `ASIGNACION_MODIFICAR`, return `ActualizarVigenciaResponse(count=N)`
  - `exportar_equipo(materia_id, carrera_id, cohorte_id, format, include_pii, current_user)` → check `include_pii` requires `equipos:ver-pii` permission (raise 403 if not). Fetch data via `_repo_equipo.get_equipo_for_export(...)`. Generate CSV (via `csv.writer` + `io.StringIO`) or XLSX (via `openpyxl.Workbook` + `io.BytesIO`). Audit log `EQUIPO_EXPORTAR`. Return `StreamingResponse` with correct Content-Type + Content-Disposition headers.

## Phase 4: Router Layer

- [x] 4.1 Create `backend/app/api/v1/routers/equipos.py` with `router = APIRouter(prefix="/api/v1/equipos", tags=["equipos"])`:
  - `GET /mis-equipos` → `Depends(get_current_active_user)` only (no permission guard). Query params: `materia_id?`, `carrera_id?`, `cohorte_id?`, `estado_vigencia?`, `limit`, `offset`. Returns `PaginatedEquipoResponse`.
  - `GET /equipo` → `Depends(require_permission("equipos:asignar"))`. Query params: `materia_id`, `carrera_id`, `cohorte_id` (all required), `estado_vigencia?`, `limit`, `offset`. Returns `PaginatedEquipoResponse`.
  - `POST /asignacion-masiva` → `equipos:asignar` guard. Body: `AsignacionMasivaRequest`. Returns 201 + `AsignacionMasivaResponse`.
  - `POST /clonar` → `equipos:asignar` guard. Body: `ClonarEquipoRequest`. Returns `ClonarEquipoResponse`.
  - `PUT /{materia_id}/{carrera_id}/{cohorte_id}/vigencia` → `equipos:asignar` guard. Body: `ActualizarVigenciaRequest` (only `desde` and `hasta` fields needed; equipo key from path). Returns `ActualizarVigenciaResponse`.
  - `GET /exportar` → `equipos:asignar` guard. Query params: `materia_id`, `carrera_id`, `cohorte_id`, `format?` (default csv), `include_pii?` (default false). Returns `StreamingResponse`.

- [x] 4.2 Modify `backend/app/api/v1/routers/asignaciones.py` — add `equipo: Annotated[bool, Query()] = False` parameter to `listar_asignaciones` endpoint. When `equipo=True`, pass through to service (informational flag for future grouping; current implementation returns same flat list filtered by materia/carrera/cohorte which already act as equipo key).

## Phase 5: Wiring

- [x] 5.1 Modify `backend/app/main.py` — import `equipos_router` from `app.api.v1.routers.equipos` and `app.include_router(equipos_router)`

## Summary

| Phase | Tasks | Focus |
|-------|-------|-------|
| Phase 1 | 2 | Schemas + dependency |
| Phase 2 | 1 | Repository with JOINs and bulk ops |
| Phase 3 | 1 | Service with business logic + audit |
| Phase 4 | 2 | Router endpoints + asignaciones modification |
| Phase 5 | 1 | Main.py registration |
| Total | 7 | |

### Implementation Order
Phase 1 → 2 → 3 → 4 → 5 (strict dependency chain: schemas needed by repo/service/router, repo needed by service, service needed by router, router needed by main.py).

### Next Step
Ready for implementation (sdd-apply).
