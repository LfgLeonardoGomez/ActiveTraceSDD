# Design: C-13 Encuentros y Guardias

## Technical Approach

Three new SQLAlchemy models (`SlotEncuentro`, `InstanciaEncuentro`, `Guardia`) with a single Alembic migration `007`. Eager materialization: creating a `SlotEncuentro` generates N `InstanciaEncuentro` rows in the same DB transaction. Slot edits are non-cascading (RN-14). A read-only HTML block endpoint renders a semantic table of instances. Guardia export reuses the existing CSV/XLSX pattern from `EquiposService` (C-08). All endpoints guarded by `encuentros:gestionar` and `guardias:registrar` with tenant isolation.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| FK creator/tutor | `creador_id` → `usuarios.id`; `tutor_id` → `usuarios.id` | `asignacion_id` (proposal/KB) | Direct user link is simpler; service still validates the user has an active assignment for the context. |
| One-off encounters | `cantidad_semanas=1` for slot-bound; standalone `InstanciaEncuentro` with `slot_id=NULL` | `cantidad_semanas=0` or `es_unico` boolean | `cantidad_semanas=1` is semantically consistent (one instance generated). Standalone mode 2 uses `slot_id=NULL` directly. |
| Instance generation | Eager bulk INSERT in same transaction | Lazy generation (on read) or background job | Required by RN-13 and specs; deterministic dates; easy to query. |
| Slot edit cascade | No cascade to existing instances | Retroactive update or soft-delete+regenerate | RN-14: each instance is independent. Users edit instances individually. |
| HTML block | Plain string template (f-strings) | Jinja2 or Markdown lib | No new dependency; simple semantic table with CSS classes. |
| Guardia export | CSV default; XLSX via `?formato=xlsx` | Only CSV, or PDF | Matches existing `EquiposService` pattern; openpyxl already available. |
| Repository layout | `SlotEncuentroRepository` + `InstanciaEncuentroRepository` in `encuentros.py` | One repo per file | Keeps related domain together; under 500 LOC. |

## Data Flow

```
POST /api/v1/encuentros/slots
  ├── Router validates permission "encuentros:gestionar"
  ├── EncuentroService.crear_slot()
  │   ├── validates materia_id (via MateriaRepository)
  │   ├── creates SlotEncuentro (repo)
  │   ├── computes N dates from fecha_inicio + dia_semana
  │   └── bulk-inserts N InstanciaEncuentro rows (repo)
  ├── single commit (slot + instances)
  └── AuditLog insert (repo_audit)

PUT /api/v1/encuentros/instancias/{id}
  ├── Router validates permission
  ├── EncuentroService.editar_instancia()
  │   └── updates only editable fields (estado, meet_url, video_url, comentario)
  └── AuditLog insert

GET /api/v1/encuentros/bloque-html
  ├── lists InstanciaEncuentro by materia_id/slot_id
  └── renders plain HTML table string

POST /api/v1/guardias
  ├── Router validates permission "guardias:registrar"
  ├── GuardiaService.registrar()
  │   ├── validates user has active assignment for (materia, carrera, cohorte)
  │   └── creates Guardia with estado=Pendiente
  └── AuditLog insert

GET /api/v1/guardias?formato=xlsx
  ├── filters by tenant + query params
  ├── GuardiaService.exportar()
  └── returns StreamingResponse (CSV or XLSX via openpyxl)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/slot_encuentro.py` | Create | `SlotEncuentro` ORM model |
| `backend/app/models/instancia_encuentro.py` | Create | `InstanciaEncuentro` ORM model |
| `backend/app/models/guardia.py` | Create | `Guardia` ORM model |
| `backend/alembic/versions/007_slot_encuentro_instancia_guardia.py` | Create | Migration: 3 tables + permission seeds |
| `backend/app/schemas/encuentros.py` | Create | Pydantic DTOs for slots and instances |
| `backend/app/schemas/guardias.py` | Create | Pydantic DTOs for guardias |
| `backend/app/repositories/encuentros.py` | Create | `SlotEncuentroRepository`, `InstanciaEncuentroRepository` |
| `backend/app/repositories/guardias.py` | Create | `GuardiaRepository` |
| `backend/app/services/encuentros.py` | Create | `EncuentroService`: create slot, generate instances, edit instance, HTML block, list/filter |
| `backend/app/services/guardias.py` | Create | `GuardiaService`: register, query, export (CSV/XLSX) |
| `backend/app/api/v1/routers/encuentros.py` | Create | Endpoints for slots, instances, HTML block |
| `backend/app/api/v1/routers/guardias.py` | Create | Endpoints for guardias CRUD + export |
| `backend/app/models/__init__.py` | Modify | Import new models |
| `backend/app/main.py` | Modify | Register `encuentros` and `guardias` routers |

## Interfaces / Contracts

### Enums

```python
# dia_semana: int 0-6 (Monday=0, per datetime.weekday)
DIA_SEMANA_MAP = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}

# InstanciaEncuentro.estado
ESTADO_INSTANCIA = ["Programado", "Realizado", "Cancelado"]

# Guardia.estado
ESTADO_GUARDIA = ["Pendiente", "Realizada"]
```

### SlotEncuentro.create flow (pseudo)

```python
async def crear_slot(data: SlotCreate, actor_id: UUID) -> SlotEncuentro:
    # validate materia exists
    # validate cantidad_semanas in [1, 52]
    slot = await slot_repo.create(...)
    instances = []
    for i in range(data.cantidad_semanas):
        fecha = compute_date(data.fecha_inicio, data.dia_semana, i)
        instances.append(InstanciaEncuentro(slot_id=slot.id, fecha=fecha, ...))
    await instance_repo.bulk_create(instances)  # same session, single commit
    return slot
```

### Guardia horario validation

```python
# Pydantic validator in GuardiaCreate
HORARIO_REGEX = r"^\d{2}:\d{2}[-–]\d{2}:\d{2}$"
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Date computation logic (`fecha_inicio + i*7` aligned to `dia_seman`) | Parametrized pytest with edge cases (year boundary, leap year) |
| Unit | Horario regex validation | Pydantic schema tests |
| Integration | Slot creation generates exact N instances | DB transaction test, assert row count |
| Integration | Slot edit does not cascade | Update slot, assert instance rows unchanged |
| Integration | Soft-delete slot cascades to instances | Set `deleted_at` on slot, assert instances also soft-deleted |
| Integration | Guardia export CSV/XLSX | Streaming response test, parse output, assert headers |
| Integration | Tenant isolation | Create data in tenant A, query from tenant B, assert 404/empty |
| E2E | Full flow: create slot → list instances → edit instance → generate HTML | FastAPI TestClient with real DB |

## Migration / Rollout

- Migration `007` creates 3 tables and seeds `encuentros:gestionar` + `guardias:registrar` to ADMIN and COORDINADOR roles.
- Rollback: downgrade drops tables; orphaned permission rows are harmless.
- No data migration required (additive change).

## Open Questions

- None
