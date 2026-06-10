# Proposal: C-08 Equipos Docentes

## Intent

Enable COORDINADOR and ADMIN to manage teaching teams at scale: bulk-assign docentes to a subject×career×cohort×role combination, clone entire teams across periods, batch-update vigencia, and export team data. Also provide each docente a personal "my teams" view. All built on top of the existing Asignacion model and CRUD from C-07.

## Scope

### In Scope
- **F4.2 Mis-equipos**: endpoint for logged-in docente to see their own assignments/teams with filters
- **F4.3 Gestión de asignaciones**: team-oriented view extending existing `/api/v1/asignaciones` with equipo-scoped queries
- **F4.4 Asignación masiva**: bulk endpoint to create N assignments for multiple docentes × same (materia, carrera, cohorte, rol, vigencia) tuple
- **F4.5 Clonar equipo entre períodos** (RN-12): duplicate all vigente assignments from a source (materia×carrera×cohorte) to a target cohorte with new vigencia dates
- **F4.6 Modificar vigencia general del equipo**: batch update `desde`/`hasta` for all assignments matching a team context
- **F4.7 Exportar equipo a archivo**: CSV/XLSX export of team assignments with all detail columns
- New router prefix `/api/v1/equipos/` with guard `equipos:asignar`
- Audit logging for all write operations (ASIGNACION_CREAR, ASIGNACION_CLONAR, ASIGNACION_MODIFICAR, EQUIPO_EXPORTAR)

### Out of Scope
- Frontend UI (covered by C-23)
- New DB models or migrations (all data fits the existing Asignacion table)
- Communication/N8N integration
- User management (covered by C-07)
- Autocompletado search UI (RN-30 logic belongs to the user-search infrastructure; the bulk endpoint accepts validated user IDs)

## Capabilities

### New Capabilities
- `equipos-mis-teams`: personal team view for docentes (F4.2)
- `equipos-bulk-operations`: bulk assign, clone, batch vigencia update, export (F4.4–F4.7)

### Modified Capabilities
- `asignaciones-rol-contexto`: extend read path with equipo-scoped filter (team = materia×carrera×cohorte) and add the `equipo` query parameter to existing list endpoint (backward-compatible addition)

## Approach

**No new models or migrations.** The Asignacion table already has every field needed (usuario_id, rol, materia_id, carrera_id, cohorte_id, comisiones, responsable_id, desde, hasta). C-08 adds service-layer operations and new route groups on top of the existing repository.

1. **EquipoService** — new service class in `services/equipos.py` that composes AsignacionRepository (read/write) and UsuarioRepository (docente validation). Uses existing repos; no direct DB access.

2. **Router** `/api/v1/equipos/` — 6 endpoints under `equipos:asignar` guard:
   - `GET /mis-equipos` — docente's own assignments (also requires auth, uses `is_propio` from PermissionContext)
   - `GET /equipo?materia_id=&carrera_id=&cohorte_id=` — team view (equipo-scoped list)
   - `POST /asignacion-masiva` — bulk create
   - `POST /clonar-equipo` — clone team to new cohorte (RN-12)
   - `PUT /vigencia-equipo` — batch vigencia update
   - `GET /exportar-equipo` — CSV/XLSX download

3. **Bulk operations** use a single DB transaction per request. If any row in a bulk create fails validation, the entire batch rolls back. No partial success.

4. **Cloning** (RN-12): copies all vigente assignments matching source (materia×carrera×cohorte) creating new rows with the target cohorte and new vigencia dates. Original assignments are never modified.

5. **Export**: streams CSV by default. XLSX via `?format=xlsx` if openpyxl is available; otherwise CSV fallback with appropriate Content-Type.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/api/v1/routers/equipos.py` | New | New router with 6 endpoints |
| `backend/app/services/equipos.py` | New | EquipoService composing existing repos |
| `backend/app/schemas/equipos.py` | New | Pydantic schemas for bulk, clone, vigencia, export |
| `backend/app/main.py` | Modified | Register equipos router |
| `backend/app/api/v1/routers/asignaciones.py` | Modified | Add `equipo` filter support to list endpoint |
| `backend/app/repositories/asignaciones.py` | Modified | Add equipo-scoped query methods |
| `backend/app/services/asignaciones.py` | Modified | (minor) expose equipo query capability |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Bulk assign creates many rows in one transaction; DB timeout on very large batches | Med | Cap bulk operations at 100 assignments per request; validate count before INSERT |
| Clone duplicates inactive (vencida) assignments by mistake | Med | Clone only filters vigente assignments (desde ≤ today AND (hasta IS NULL OR hasta ≥ today)); dry-run preview returns count before actual clone |
| Batch vigencia update changes assignments that should not be touched (e.g. vencida intentionally) | Med | Only update assignments where estado_vigencia is "Vigente" at query time; validation rejects if no vigente assignments match |
| Export includes PII from Usuario (email, dni) | Low | Export only includes non-PII fields (nombre, apellidos, rol, materia, carrera, cohorte, comisiones, vigencia, estado); PII requires separate `equipos:ver-pii` permission |
| Race condition on bulk create — another admin creates overlapping assignments simultaneously | Low | No uniqueness constraint on (usuario, rol, materia, carrera, cohorte) per RN; allow overlapping, surface duplicates in response with a warning flag |

## Rollback Plan

- No schema changes → no migration rollback needed
- Remove `equipos` router from `main.py`, delete `services/equipos.py`, `schemas/equipos.py`, `routers/equipos.py`
- Revert minor changes to `asignaciones.py` router (equipo filter) and repository
- All changes are additive; removal is safe

## Dependencies

- **C-07** (completed): Asignacion model, repository, service, schemas — foundation for everything
- **C-06** (completed): Carrera, Cohorte, Materia models — FK targets in equipo queries
- **C-04** (completed): RBAC permission guard `equipos:asignar` — already seeded
- **C-05** (completed): Audit log — action codes for equipo operations

## Success Criteria

- [ ] Docente can GET their own assignments filtered by their user_id via `/mis-equipos`
- [ ] COORDINADOR/ADMIN can bulk-assign 10+ docentes in a single request and all rows appear in DB
- [ ] Cloning a team of 5 assignments creates 5 new rows with target cohorte and new dates; originals unchanged
- [ ] Batch vigencia update changes `desde`/`hasta` on all vigente assignments of a team atomically
- [ ] Export produces valid CSV with correct columns and tenant isolation
- [ ] All write endpoints generate audit log entries
- [ ] No new DB migrations required (all data fits existing Asignacion table)