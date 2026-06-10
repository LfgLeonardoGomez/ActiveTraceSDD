# Tasks: C-13 Encuentros y Guardias

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1400–1500 (14 new files + 2 modifications) |
| 800-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (models + migration + schemas + repos) → PR 2 (services + routers + registration) |
| Delivery strategy | single-pr (user override — size:exception implied) |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: size-exception
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Domain layer: models, migration, schemas, repositories | PR 1 | ~800 lines; foundation with no runtime behavior |
| 2 | Business + API: services, routers, main.py registration | PR 2 | ~650 lines; depends on PR 1 |

## Phase 1: Models + Migration

- [x] 1.1 Create `backend/app/models/slot_encuentro.py` — `SlotEncuentro` model extending `BaseModelMixin, Base`. Fields: `creador_id` (FK → usuarios.id), `materia_id` (FK → materias.id), `titulo` (Text), `dia_semana` (Integer 0-6), `hora` (Text HH:MM), `fecha_inicio` (Date), `cant_semanas` (Integer 1-52), `meet_url` (Text nullable), `vigencia` (Text nullable). Indexes on tenant_id, materia_id, creador_id. `lazy="raise"` on relationships.
- [x] 1.2 Create `backend/app/models/instancia_encuentro.py` — `InstanciaEncuentro` model extending `BaseModelMixin, Base`. Fields: `slot_id` (FK → slot_encuentros.id, nullable for one-offs), `materia_id` (FK → materias.id), `titulo` (Text nullable), `fecha` (Date), `hora` (Text HH:MM), `estado` (String(20) default "Programado"), `meet_url` (Text nullable), `video_url` (Text nullable), `comentario` (Text nullable). Indexes on tenant_id, slot_id, materia_id, fecha.
- [x] 1.3 Create `backend/app/models/guardia.py` — `Guardia` model extending `BaseModelMixin, Base`. Fields: `tutor_id` (FK → usuarios.id), `materia_id` (FK → materias.id), `carrera_id` (FK → carreras.id), `cohorte_id` (FK → cohortes.id), `fecha` (Date), `horario` (Text nullable), `descripcion` (Text), `estado` (String(20) default "Pendiente"), `comentarios` (Text nullable). Indexes on tenant_id, tutor_id, materia_id.
- [x] 1.4 Update `backend/app/models/__init__.py` — add imports for `SlotEncuentro`, `InstanciaEncuentro`, `Guardia` and append to `__all__`.
- [x] 1.5 Create `backend/alembic/versions/007_slot_encuentro_instancia_guardia.py` — migration creating 3 tables (`slot_encuentros`, `instancias_encuentro`, `guardias`) with all columns, FKs, and indexes. Seed permissions: `encuentros:gestionar` → PROFESOR, TUTOR, COORDINADOR, ADMIN; `guardias:registrar` → TUTOR, PROFESOR, COORDINADOR, ADMIN. `down_revision = "006_usuario_pii_asignacion"`. Downgrade drops tables and removes permission seeds.

## Phase 2: Schemas

- [x] 2.1 Create `backend/app/schemas/encuentros.py` — Pydantic v2 DTOs all with `extra="forbid"`: `SlotCreate` (materia_id, dia_semana 0-6, hora regex HH:MM, fecha_inicio, cant_semanas 1-52, titulo?, meet_url?), `SlotRead`, `SlotUpdate` (titulo?, meet_url?), `InstanciaCreate` (materia_id, fecha, hora, titulo?, meet_url?), `InstanciaRead`, `InstanciaUpdate` (estado enum Programado/Realizado/Cancelado, meet_url?, video_url?, comentario?), `InstanciaFilterParams` (materia_id?, slot_id?, estado?, fecha_desde?, fecha_hasta?), `PaginatedInstanciaResponse`, `PaginatedSlotResponse`.
- [x] 2.2 Create `backend/app/schemas/guardias.py` — Pydantic v2 DTOs all with `extra="forbid"`: `GuardiaCreate` (materia_id, carrera_id, cohorte_id, fecha, horario? with regex `^\d{2}:\d{2}[-–]\d{2}:\d{2}$`, descripcion), `GuardiaRead`, `GuardiaFilterParams` (materia_id?, tutor_id?, estado?, fecha_desde?, fecha_hasta?), `PaginatedGuardiaResponse`, `ExportarGuardiasParams` (formato csv|xlsx).

## Phase 3: Repositories

- [x] 3.1 Create `backend/app/repositories/encuentros.py` — `SlotEncuentroRepository(BaseRepository[SlotEncuentro])` with: `list_slots` (paginated, filters by materia_id), `bulk_create_instancias` (add_all + flush, no commit). `InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro])` with: `list_instancias` (paginated, filters: materia_id, slot_id, estado, fecha_desde, fecha_hasta), `update_instancia`, `soft_delete_by_slot_id` (cascade soft-delete instances when slot is deleted).
- [x] 3.2 Create `backend/app/repositories/guardias.py` — `GuardiaRepository(BaseRepository[Guardia])` with: `list_guardias` (paginated, filters: materia_id, tutor_id, estado, fecha_desde, fecha_hasta), `get_guardias_for_export` (JOIN with Usuario/Materia/Carrera/Cohorte for enriched names, non-PII only).

## Phase 4: Services

- [x] 4.1 Create `backend/app/services/encuentros.py` — `EncuentroService(db_session, tenant_id)`. Methods: `crear_slot(data, actor_id)` — validates materia exists, creates slot + bulk-inserts N instances (date computation: `fecha_inicio + i*7` aligned to `dia_semana`), single commit, audit log. `crear_instancia_unica(data, actor_id)` — standalone instance with slot_id=NULL. `editar_instancia(id, data, actor_id)` — update editable fields only. `listar_instancias(filters, limit, offset)`. `listar_slots(materia_id, limit, offset)`. `actualizar_slot(id, data, actor_id)` — slot fields only, no cascade. `eliminar_slot(id, actor_id)` — soft-delete slot + cascade soft-delete instances. `generar_bloque_html(materia_id, slot_id?, formato)` — returns HTML table or Markdown string of upcoming instances.
- [x] 4.2 Create `backend/app/services/guardias.py` — `GuardiaService(db_session, tenant_id)`. Methods: `registrar_guardia(data, current_user)` — validates user has active Asignacion for context, creates Guardia estado=Pendiente, audit log. `listar_guardias(filters, limit, offset, current_user)` — scope-filtered: COORDINADOR/ADMIN see all tenant guardias; TUTOR/PROFESOR see only own. `exportar_guardias(filters, formato, current_user)` — CSV or XLSX via openpyxl StreamingResponse, non-PII fields.

## Phase 5: Routers

- [x] 5.1 Create `backend/app/api/v1/routers/encuentros.py` — `APIRouter(prefix="/api/v1/encuentros", tags=["encuentros"])`. Endpoints: `POST /slots` (crear slot → encuentros:gestionar), `GET /slots` (listar slots → encuentros:gestionar), `GET /slots/{id}` (obtener slot), `PUT /slots/{id}` (actualizar slot), `DELETE /slots/{id}` (soft-delete slot), `POST /instancias` (crear instancia única → encuentros:gestionar), `GET /instancias` (listar instancias con filtros), `PUT /instancias/{id}` (editar instancia), `GET /bloque-html` (generar HTML/Markdown block). All use `require_permission("encuentros:gestionar")` and `CurrentUser` dependency.
- [x] 5.2 Create `backend/app/api/v1/routers/guardias.py` — `APIRouter(prefix="/api/v1/guardias", tags=["guardias"])`. Endpoints: `POST /` (registrar guardia → guardias:registrar), `GET /` (listar guardias con filtros y export via ?formato=), `GET /{id}` (obtener guardia). List/export endpoint uses `require_permission("guardias:registrar")`.

## Phase 6: Registration

- [x] 6.1 Update `backend/app/main.py` — import `encuentros_router` and `guardias_router`, add `app.include_router()` calls after existing router registrations.
