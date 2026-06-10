# Design: C-08 Equipos Docentes

## Technical Approach

Build on the existing `Asignacion` model (C-07). Create `EquipoService` and `EquipoRepository` (new files) to handle team-scoped queries with JOINs, bulk operations, clone, and export. New router at `/api/v1/equipos/` with 6 endpoints. No new models or migrations.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Equipo key | Composite `(materia_id, carrera_id, cohorte_id)` | New `equipos` table | No schema changes needed; all data fits in `Asignacion` |
| Repository strategy | New `EquipoRepository` for joins/bulk; reuse existing repos for single-model CRUD | Modify `AsignacionRepository` | Keeps Clean Architecture; avoids cross-cutting changes to stable repo |
| Bulk atomicity | `EquipoRepository.bulk_create` uses `add_all` + `flush`; service commits once | Repo commits per row | Atomic rollback on any validation failure |
| Clone behavior | INSERT new rows only; originals untouched | Update original rows | RN-12 requires preserving historical assignments |
| Export format | CSV default (`text/csv`); XLSX via `openpyxl` if available | Always XLSX | CSV is dependency-free, streamable, universally compatible |
| PII in export | Excluded by default; requires `equipos:ver-pii` | Always include | Principle of least privilege |
| Response enrichment | `EquipoRepository` does explicit JOINs with `Materia`, `Carrera`, `Cohorte` | N+1 queries in service | Single query per list; no N+1 |

## Data Flow

```
Request → Router (auth/guard) → EquipoService → Repositories → PostgreSQL
                                              ↓
                                         AuditLog (write ops only)
```

- **mis-equipos**: Auth only (no permission guard) → `EquipoService.mis_equipos` → `EquipoRepository.list_by_usuario_with_names`
- **asignacion-masiva**: `equipos:asignar` guard → validate all `usuario_ids` via `UsuarioRepository` → `EquipoRepository.bulk_create` → `AuditLogRepository.insert(ASIGNACION_CREAR)`
- **clonar**: `equipos:asignar` guard → preview count or execute → `EquipoRepository.clone_vigente` → `AuditLogRepository.insert(ASIGNACION_CLONAR)`
- **vigencia**: `equipos:asignar` guard → `EquipoRepository.update_vigencia_by_equipo` → `AuditLogRepository.insert(ASIGNACION_MODIFICAR)`
- **exportar**: `equipos:asignar` guard → `EquipoRepository.get_equipo_for_export` → CSV/XLSX stream → `AuditLogRepository.insert(EQUIPO_EXPORTAR)`

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/services/equipos.py` | Create | `EquipoService` composing 6 repositories |
| `backend/app/repositories/equipos.py` | Create | `EquipoRepository` with JOINs, bulk insert, clone, export queries |
| `backend/app/schemas/equipos.py` | Create | Pydantic schemas for all 6 endpoints |
| `backend/app/api/v1/routers/equipos.py` | Create | 6 endpoints under `/api/v1/equipos/` |
| `backend/app/main.py` | Modify | Register `equipos_router` |

## Interfaces / Contracts

### Schemas

```python
class EquipoRead(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID; tenant_id: UUID; usuario_id: UUID; rol: str
    desde: date; hasta: date | None
    materia_id: UUID | None; carrera_id: UUID | None; cohorte_id: UUID | None
    comisiones: list[str] | None; responsable_id: UUID | None
    estado_vigencia: str
    materia_nombre: str | None; carrera_nombre: str | None; cohorte_nombre: str | None
    usuario_nombre: str | None; usuario_apellidos: str | None

class AsignacionMasivaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usuario_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    materia_id: UUID; carrera_id: UUID; cohorte_id: UUID
    rol: str = Field(..., min_length=1)
    desde: date; hasta: date | None = None

class AsignacionMasivaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    count: int; created_ids: list[UUID]

class ClonarEquipoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: UUID; carrera_id: UUID
    cohorte_id_origen: UUID; cohorte_id_destino: UUID
    desde: date; hasta: date | None = None
    preview: bool = False

class ClonarEquipoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preview_count: int
    created_count: int | None = None
    created_ids: list[UUID] | None = None

class ActualizarVigenciaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: UUID; carrera_id: UUID; cohorte_id: UUID
    desde: date; hasta: date | None = None

class ActualizarVigenciaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    count: int

class EquipoFilterParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: UUID | None = None; carrera_id: UUID | None = None
    cohorte_id: UUID | None = None; estado_vigencia: str | None = None

class PaginatedEquipoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[EquipoRead]; total: int; limit: int; offset: int
```

### Service

```python
class EquipoService:
    def __init__(self, db: AsyncSession, tenant_id: UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo_asig = AsignacionRepository(db, tenant_id)
        self._repo_user = UsuarioRepository(db, tenant_id)
        self._repo_mat = MateriaRepository(db, tenant_id)
        self._repo_car = CarreraRepository(db, tenant_id)
        self._repo_coh = CohorteRepository(db, tenant_id)
        self._repo_audit = AuditLogRepository(db, tenant_id)
        self._repo_equipo = EquipoRepository(db, tenant_id)

    async def mis_equipos(self, current_user, filters, limit, offset) -> tuple[list[EquipoRead], int]: ...
    async def asignacion_masiva(self, data, current_user) -> AsignacionMasivaResponse: ...
    async def clonar_equipo(self, data, current_user) -> ClonarEquipoResponse: ...
    async def actualizar_vigencia(self, data, current_user) -> ActualizarVigenciaResponse: ...
    async def exportar_equipo(self, data, current_user, format, include_pii) -> StreamingResponse: ...
```

### Router Endpoints

| Method | Path | Guard | Description |
|--------|------|-------|-------------|
| GET | `/api/v1/equipos/mis-equipos` | Auth only | Docente's own assignments |
| GET | `/api/v1/equipos/equipo` | `equipos:asignar` | Team view by composite key |
| POST | `/api/v1/equipos/asignacion-masiva` | `equipos:asignar` | Bulk create (max 100) |
| POST | `/api/v1/equipos/clonar` | `equipos:asignar` | Clone vigente assignments |
| PUT | `/api/v1/equipos/vigencia` | `equipos:asignar` | Batch update vigencia |
| GET | `/api/v1/equipos/exportar` | `equipos:asignar` | CSV/XLSX download |

## Audit Log

All write operations generate `AuditLog` entries via `AuditLogRepository.insert` (flush only, no commit — participates in the service transaction).

| Operation | Action Code | Detail |
|-----------|-------------|--------|
| asignacion-masiva | `ASIGNACION_CREAR` | `filas_afectadas` = count, `detalle` = team key |
| clonar | `ASIGNACION_CLONAR` | `filas_afectadas` = cloned count, `detalle` = source→target |
| vigencia | `ASIGNACION_MODIFICAR` | `filas_afectadas` = updated count, `detalle` = new dates |
| exportar | `EQUIPO_EXPORTAR` | `filas_afectadas` = exported count, `detalle` = format + PII flag |

## Testing Strategy

Skipped per task instruction.

## Migration / Rollout

No migration required — all data fits in the existing `Asignacion` table. Rollback: remove router from `main.py`, delete new files.

## Open Questions

- [ ] The spec `asignaciones-rol-contexto` requires adding `equipo` query parameter to the existing `/api/v1/asignaciones` list endpoint. This requires modifying `backend/app/api/v1/routers/asignaciones.py` and `backend/app/repositories/asignaciones.py`. Should this be included in C-08 or deferred to a separate micro-task?
- [ ] The spec uses `PUT /api/v1/equipos/{equipo_id}/vigencia` but there is no `equipo_id` UUID. The design uses `PUT /api/v1/equipos/vigencia` with composite key in the body. Confirm path with product.
- [ ] XLSX export: should `openpyxl` be added as a project dependency or kept as an optional extra?
