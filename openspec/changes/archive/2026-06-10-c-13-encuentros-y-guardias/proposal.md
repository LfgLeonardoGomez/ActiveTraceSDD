# Proposal: C-13 Encuentros y Guardias

## Intent

Enable PROFESOR and COORDINADOR to plan recurring and one-off synchronous academic encounters (virtual classes, meetings) and generate instances automatically from a weekly slot definition. Enable TUTOR to register guardias (duty shifts) and COORDINADOR/ADMIN to query and export guardia records globally. Produce an HTML block suitable for embedding in Moodle virtual classrooms. All scoped per-tenant with RBAC guards.

## Scope

### In Scope
- **F6.1 Crear encuentro recurrente**: define `SlotEncuentro` (day, time, start date, week count) → system generates N `InstanciaEncuentro` rows automatically (RN-13, mode 1)
- **F6.2 Crear encuentro único**: single `InstanciaEncuentro` without a slot parent (RN-13, mode 2)
- **F6.3 Editar instancia**: modify estado (`Programado`|`Realizado`|`Cancelado`), meet_url, video_url, comentario per instance (RN-14: each instance is independent)
- **F6.4 Generar bloque HTML**: endpoint returning a formatted HTML fragment of scheduled encounters for a given materia/slot, ready to paste into Moodle's virtual classroom
- **F6.5 Vista admin de encuentros**: COORDINADOR/ADMIN cross-tenant view of all encounters with filters
- **F6.6 Registro de guardias**: TUTOR registers own guardias; COORDINADOR/ADMIN queries globally + export (CSV/XLSX)
- New models: `SlotEncuentro`, `InstanciaEncuentro`, `Guardia` with migration
- New routers: `/api/v1/encuentros/`, `/api/v1/guardias/` with `encuentros:gestionar` and `guardias:registrar` permission guards
- Audit logging for all write operations

### Out of Scope
- Frontend UI (covered by C-23)
- N8N/Moodle WS integration for HTML block publishing (manual copy-paste is F6.4's intent)
- Videoconferencing room provisioning (meet_url is stored, not created)
- Notification/alert when an encounter is approaching
- Coloquios/Evaluaciones (separate change C-14)
- Recurring edit (editing slot → propagating to all future instances) — future enhancement

## Capabilities

### New Capabilities
- `encuentros-crud`: create slots, generate instances, edit instances, generate HTML block (F6.1–F6.5)
- `guardias-registro`: register guardias, query globally, export (F6.6)

### Modified Capabilities
- None — no existing specs are modified at the requirement level

## Approach

1. **Models + Migration**: Three new SQLAlchemy models following existing conventions (BaseModelMixin, tenant_id, UUID PK, soft delete). Migration `007_slot_encuentro_instancia_guardia`.
   - `SlotEncuentro`: stores recurring definition (materia_id, dia_semana, hora, fecha_inicio, cant_semanas, meet_url, titulo, vigencia). FK to `asignaciones.id` (creator) and `materias.id`.
   - `InstanciaEncuentro`: concrete instance derived from slot or created standalone. FK to `slot_encuentro.id` (nullable for one-offs), `materias.id`. estado enum (Programado, Realizado, Cancelado). meet_url, video_url, comentario.
   - `Guardia`: duty shift record. FK to `asignaciones.id` (who covered), `materias.id`, `carreras.id`, `cohortes.id`. dia enum, horario text, estado enum (Pendiente, Realizada, Cancelada), comentarios.

2. **Slot → Instance generation** (RN-13, mode 1): When creating a `SlotEncuentro` with `cant_semanas > 0`, the service layer computes N dates starting from `fecha_inicio` advancing by `dia_semana` weekly and creates N `InstanciaEncuentro` rows in a single transaction. Mode 2 (`fecha_unica` or `cant_semanas == 0`) creates exactly one instance.

3. **Service layer**: `EncuentroService` (create slot with instance generation, edit instance, generate HTML, list/filter) and `GuardiaService` (register, query with filters, export). Both compose existing repositories. No direct DB access.

4. **RBAC**: Two permission codes seeded — `encuentros:gestionar` (PROFESOR `(propio)`, TUTOR, COORDINADOR, ADMIN per matrix) and `guardias:registrar` (TUTOR `(propio)`, PROFESOR `(propio)`, COORDINADOR, ADMIN). The `(propio)` modifier filters by the user's asignacion scope.

5. **HTML block generation**: Service method `generate_html_block(materia_id, slot_id=None)` returns a structured HTML fragment with a table of upcoming instances (date, time, title, meet_url link, video_url if available). Plaintext/markdown alternative via `?format=markdown` query param.

6. **Guardia export**: CSV by default, XLSX via `?format=xlsx` query param. Includes non-PII fields: tutor name, materia, carrera, cohorte, dia, horario, estado, comentarios.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/slot_encuentro.py` | New | SlotEncuentro ORM model |
| `backend/app/models/instancia_encuentro.py` | New | InstanciaEncuentro ORM model |
| `backend/app/models/guardia.py` | New | Guardia ORM model |
| `backend/alembic/versions/007_*.py` | New | Migration for 3 tables |
| `backend/app/repositories/encuentros.py` | New | Slot + Instance repository |
| `backend/app/repositories/guardias.py` | New | Guardia repository |
| `backend/app/services/encuentros.py` | New | Business logic: create slot, generate instances, edit instance, HTML block |
| `backend/app/services/guardias.py` | New | Business logic: register, query, export |
| `backend/app/api/v1/routers/encuentros.py` | New | Endpoints for encounters |
| `backend/app/api/v1/routers/guardias.py` | New | Endpoints for guardias |
| `backend/app/schemas/encuentros.py` | New | Pydantic request/response DTOs |
| `backend/app/schemas/guardias.py` | New | Pydantic request/response DTOs |
| `backend/app/main.py` | Modified | Register new routers |
| `backend/app/models/__init__.py` | Modified | Import new models |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Instance generation creates many rows in one transaction (e.g. 52 weeks) | Low | Cap `cant_semanas` at 52; validate before INSERT |
| Editing slot-level fields (time, day) after instances exist creates ambiguity | Med | Slot edits only affect the slot definition; existing instances are NOT retroactively updated. Users edit individual instances if needed (RN-14) |
| HTML block format may not match all LMS themes | Low | Return semantic HTML table with CSS classes; institutions can style. No inline styles |
| Guardia `horario` as free-text may be inconsistent | Low | Validate format in Pydantic schema (`HH:MM–HH:MM` regex); reject malformed |
| Race condition: two proxys creating slots for same materia simultaneously | Low | No uniqueness constraint on SlotEncuentro(materia, dia, hora) per business rule; both slots coexist |

## Rollback Plan

- Drop the 3 new tables via downgrade migration
- Remove `encuentros` and `guardias` routers from `main.py`
- Delete new model, repository, service, schema, and router files
- Remove `encuentros:gestionar` and `guardias:registrar` from permission seed (or leave as orphaned entries)
- All changes are additive; rollback is safe

## Dependencies

- **C-07** (completed): `Asignacion` model + repository + service — FK target for SlotEncuentro.asignacion_id and Guardia.asignacion_id
- **C-06** (completed): `Carrera`, `Cohorte`, `Materia` models — FK targets and filter dimensions
- **C-04** (completed): RBAC permission guard infrastructure — `require_permission()`
- **C-05** (completed): Audit log — action codes for encounter/guardia operations

## Success Criteria

- [ ] Creating a recurrent slot with `cant_semanas=8` generates exactly 8 `InstanciaEncuentro` rows on the correct weekday/dates
- [ ] Creating a one-off encounter creates exactly 1 `InstanciaEncuentro` with `slot_id=NULL`
- [ ] Editing an instance's estado, meet_url, video_url, or comentario does not affect other instances or the slot (RN-14)
- [ ] HTML block endpoint returns valid HTML with instances table for a given materia
- [ ] TUTOR can register a guardia for their own asignacion; COORDINADOR/ADMIN can query all guardias cross-tenant-scope
- [ ] Guardia export produces valid CSV with non-PII fields
- [ ] All write endpoints generate audit log entries
- [ ] Multi-tenant isolation: tenant A never sees tenant B's encounters or guardias