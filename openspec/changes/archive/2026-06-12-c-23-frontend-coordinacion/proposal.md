# Proposal: C-23 — Frontend Coordinación

## Intent

Enable the **COORDINADOR** and **ADMIN** roles to manage the full academic administration lifecycle through the SPA: configure teaching teams (equipos docentes), plan and monitor encounters (encuentros), manage colloquium calls (coloquios), handle the internal task workflow (tareas), and publish system-wide announcements (avisos). Also covers the transversal monitoring views (F2.7, F2.9) and the semester setup flow (FL-03).

This change consumes five backend feature sets: **C-08** (equipos docentes), **C-13** (avisos), **C-14** (tareas internas), **C-15** (encuentros), **C-16** (coloquios). It builds on the shell established by **C-21** and follows the same architectural pattern as **C-22**.

## Scope

All features listed below map to functions defined in `knowledge-base/06_funcionalidades.md`:

| # | Funcionalidad | KB Ref | Backend API |
|---|--------------|--------|-------------|
| Épica 4 — Gestión de Equipos Docentes |
| 1 | ABM usuarios del equipo docente (ADMIN) | F4.1 | `GET/POST/PUT /api/v1/equipos/usuarios` |
| 2 | Vista de mis equipos (propia del docente) | F4.2 | `GET /api/v1/equipos/mis-equipos` |
| 3 | Consulta y gestión de asignaciones individuales | F4.3 | `GET/POST /api/v1/equipos/asignaciones` |
| 4 | Asignación masiva de docentes | F4.4 | `POST /api/v1/equipos/asignaciones/masiva` |
| 5 | Clonar equipo docente entre períodos | F4.5 | `POST /api/v1/equipos/clonar` |
| 6 | Modificar vigencia general del equipo | F4.6 | `PUT /api/v1/equipos/vigencia` |
| 7 | Exportar equipo docente | F4.7 | `GET /api/v1/equipos/export` |
| Épica 5 — Estructura Académica |
| 8 | ABM carreras | F5.1 | `GET/POST/PUT /api/v1/estructura/carreras` |
| 9 | ABM cohortes | F5.2 | `GET/POST/PUT /api/v1/estructura/cohortes` |
| 10 | Programas de materias (upload docs) | F5.3 | `GET/POST /api/v1/estructura/programas` |
| 11 | Fechas de evaluaciones | F5.4 | `GET/POST/PUT /api/v1/estructura/evaluaciones` |
| Épica 6 — Encuentros y Disponibilidad |
| 12 | Crear encuentro recurrente | F6.1 | `POST /api/v1/encuentros/recurrente` |
| 13 | Crear encuentro único | F6.2 | `POST /api/v1/encuentros` |
| 14 | Editar instancia de encuentro | F6.3 | `PUT /api/v1/encuentros/{id}` |
| 15 | Generar contenido aula virtual | F6.4 | `GET /api/v1/encuentros/contenido-aula` |
| 16 | Vista transversal de encuentros | F6.5 | `GET /api/v1/encuentros` |
| 17 | Registro y consulta de guardias | F6.6 | `GET/POST /api/v1/encuentros/guardias` |
| Épica 7 — Coloquios |
| 18 | Panel de métricas de coloquios | F7.1 | `GET /api/v1/coloquios/metricas` |
| 19 | Importar alumnos a convocatoria | F7.2 | `POST /api/v1/coloquios/importar-alumnos` |
| 20 | Crear convocatoria de coloquio | F7.3 | `POST /api/v1/coloquios` |
| 21 | Listado de convocatorias | F7.4 | `GET /api/v1/coloquios` |
| 22 | Admin global de coloquios | F7.5 | `GET/PUT /api/v1/coloquios/admin` |
| Épica 8 — Workflow de Tareas Internas |
| 23 | Vista de mis tareas | F8.1 | `GET /api/v1/tareas/mis-tareas` |
| 24 | Asignar tarea a docente | F8.2 | `POST /api/v1/tareas` |
| 25 | Admin global de tareas | F8.3 | `GET/PUT /api/v1/tareas` |
| Épica 2 — Monitoreo transversal |
| 26 | Monitor general (cruzado) | F2.7 | `GET /api/v1/analisis/monitor/general` |
| 27 | Auditoría de actividad por docente | F2.9 | `GET /api/v1/analisis/monitor/auditoria` |

## User Flows

### Flow A — Setup de inicio de cuatrimestre (FL-03)
1. **COORDINADOR** logs in → sidebar shows `/coordinacion` entry
2. Creates new cohorte via `Estructura` → `POST /api/v1/estructura/cohortes`
3. Clones previous equipo docente via `Equipos → Clonar` → selects origen + destino
4. Adjusts individual assignments via `Equipos → Asignaciones`
5. Adjusts team vigencia if needed via `Equipos → Vigencia`
6. Uploads program documents via `Estructura → Programas`
7. Sets evaluation dates via `Estructura → Evaluaciones`
8. Publishes welcome announcement via `Avisos → Nuevo aviso`

### Flow B — Encuentros recurrentes (FL-06) + Guardias
1. Teacher (or COORDINADOR) creates recurrent series via `Encuentros → Recurrente`
2. System generates instances automatically
3. Teacher marks meetings as done, adds recording URLs
4. **COORDINADOR** audits via `Encuentros → Vista transversal`
5. Tutors register guardias via `Encuentros → Guardias`
6. COORDINADOR/ADMIN views consolidated guardias

### Flow C — Coloquios (FL-07)
1. **COORDINADOR/ADMIN** opens `Coloquios` → sees metrics dashboard (F7.1)
2. Imports student roster for a convocatoria (F7.2)
3. Creates convocatoria with days and slots (F7.3)
4. Views list with operational metrics (F7.4)
5. ADMIN accesses global management (F7.5)

### Flow D — Workflow de Tareas (FL-05)
1. **COORDINADOR** creates a tarea → assigns to PROFESOR/TUTOR (F8.2)
2. Task appears in assigned teacher's panel (F8.1)
3. Teacher updates state, adds comments
4. COORDINADOR reviews, approves or returns with observations (F8.3)

### Flow E — Publicación de avisos (FL-09)
1. **COORDINADOR/ADMIN** opens `Avisos → Nuevo aviso`
2. Defines: alcance (global/materia/cohorte), roles destinatarios, severidad, contenido, ventana de visibilidad, requiere ack
3. Publishes → targets see it based on rol + alcance + cohorte
4. If `require_ack = true`, users must acknowledge

## Architecture

### Routing

```tsx
// Added to App.tsx under <Route element={<Layout />}>
<Route path="/coordinacion" element={<CoordinacionLayout />}>
  <Route index element={<CoordinacionHome />} />
  <Route path="equipos" element={<EquiposLayout />}>
    <Route index element={<MisEquipos />} />
    <Route path="usuarios" element={<AdminUsuarios />} />
    <Route path="asignaciones" element={<AsignacionesList />} />
    <Route path="asignaciones/masiva" element={<AsignacionMasiva />} />
    <Route path="clonar" element={<ClonarEquipo />} />
    <Route path="vigencia" element={<VigenciaEquipo />} />
    <Route path="exportar" element={<ExportarEquipo />} />
  </Route>
  <Route path="estructura" element={<EstructuraLayout />}>
    <Route index element={<EstructuraHome />} />
    <Route path="carreras" element={<CarrerasList />} />
    <Route path="cohortes" element={<CohortesList />} />
    <Route path="programas" element={<ProgramasList />} />
    <Route path="evaluaciones" element={<EvaluacionesList />} />
  </Route>
  <Route path="encuentros" element={<EncuentrosLayout />}>
    <Route index element={<EncuentrosList />} />
    <Route path="nuevo" element={<CrearEncuentro />} />
    <Route path="recurrente" element={<CrearRecurrente />} />
    <Route path=":encuentroId/editar" element={<EditarEncuentro />} />
    <Route path="guardias" element={<GuardiasList />} />
  </Route>
  <Route path="coloquios" element={<ColoquiosLayout />}>
    <Route index element={<ColoquiosDashboard />} />
    <Route path="nuevo" element={<CrearConvocatoria />} />
    <Route path=":convocatoriaId" element={<ConvocatoriaDetail />} />
    <Route path="admin" element={<ColoquiosAdmin />} />
  </Route>
  <Route path="tareas" element={<TareasLayout />}>
    <Route index element={<MisTareas />} />
    <Route path="asignar" element={<AsignarTarea />} />
    <Route path="admin" element={<TareasAdmin />} />
  </Route>
  <Route path="avisos" element={<AvisosLayout />}>
    <Route index element={<AvisosList />} />
    <Route path="nuevo" element={<CrearAviso />} />
    <Route path=":avisoId/editar" element={<EditarAviso />} />
  </Route>
  <Route path="monitor" element={<MonitorLayout />}>
    <Route index element={<MonitorGeneral />} />
    <Route path="auditoria" element={<AuditoriaDocente />} />
  </Route>
</Route>
```

### Navigation
- Sidebar gets a new section group `Coordinación` with entries:
  - `Equipos Docentes` — `/coordinacion/equipos` — `equipos:ver`
  - `Estructura` — `/coordinacion/estructura` — `estructura:gestionar`
  - `Encuentros` — `/coordinacion/encuentros` — `encuentros:ver`
  - `Coloquios` — `/coordinacion/coloquios` — `coloquios:ver`
  - `Tareas` — `/coordinacion/tareas` — `tareas:ver`
  - `Avisos` — `/coordinacion/avisos` — `avisos:ver`
  - `Monitor` — `/coordinacion/monitor` — `monitor:ver`

### Data Flow
- All data fetching via TanStack Query hooks with `queryKey` scoped by domain entity (e.g. `['equipos', materiaId]`, `['coloquios', convocatoriaId]`)
- Mutations via `useMutation` with `onSuccess` invalidation of related queries
- File uploads (programas, import alumnos) via FormData through Axios
- CSV exports via direct window.open or download blob from Axios response
- Recurrent instance generation: optimistic UI with progress indicator, backend processes synchronously
- Task workflow: real-time state transitions via `refetchInterval` while task is in non-terminal state

## Directory Structure

```
frontend/src/features/
└── coordinacion/
    ├── components/
    │   ├── equipos/
    │   │   ├── EquipoCard.tsx              (team summary card)
    │   │   ├── EquipoTable.tsx             (team assignments table)
    │   │   ├── AsignacionForm.tsx          (individual assignment form)
    │   │   ├── AsignacionMasivaForm.tsx    (bulk assignment with multi-select)
    │   │   ├── ClonarEquipoForm.tsx        (origen → destino selector)
    │   │   ├── VigenciaEditor.tsx          (date range editor)
    │   │   ├── ExportButton.tsx
    │   │   ├── UsuarioForm.tsx             (ADMIN: create/edit user)
    │   │   └── UsuarioTable.tsx            (ADMIN: user list)
    │   ├── estructura/
    │   │   ├── CarreraForm.tsx             (ABM carrera)
    │   │   ├── CohorteForm.tsx             (ABM cohorte)
    │   │   ├── ProgramaUploader.tsx        (file upload + metadata)
    │   │   ├── EvaluacionForm.tsx          (date entry form)
    │   │   └── EvaluacionCalendar.tsx      (calendar view)
    │   ├── encuentros/
    │   │   ├── EncuentroForm.tsx           (single encounter form)
    │   │   ├── EncuentroRecurrenteForm.tsx (series config)
    │   │   ├── EncuentroTable.tsx          (transversal list)
    │   │   ├── EncuentroEditModal.tsx      (inline edit)
    │   │   ├── ContenidoAulaPreview.tsx    (formatted output)
    │   │   └── GuardiaTable.tsx            (guardias list)
    │   ├── coloquios/
    │   │   ├── MetricasPanel.tsx           (KPI cards)
    │   │   ├── ConvocatoriaForm.tsx        (create convocatoria)
    │   │   ├── ImportarAlumnosUploader.tsx (file upload)
    │   │   ├── ConvocatoriaTable.tsx       (list with metrics)
    │   │   └── ConvocatoriaDetail.tsx      (detail + reservations)
    │   ├── tareas/
    │   │   ├── TareaCard.tsx               (my task card)
    │   │   ├── TareaForm.tsx               (create/assign task)
    │   │   ├── TareaTable.tsx              (admin list)
    │   │   ├── TareaCommentThread.tsx      (comments timeline)
    │   │   └── TareaStatusBadge.tsx        (state machine badge)
    │   ├── avisos/
    │   │   ├── AvisoForm.tsx               (create/edit with all fields)
    │   │   ├── AvisoCard.tsx               (list item)
    │   │   └── AvisoScopeSelector.tsx      (global/materia/cohorte picker)
    │   └── monitor/
    │       ├── MonitorGeneralTable.tsx     (cross-commission monitor)
    │       ├── AuditoriaTable.tsx          (activity audit)
    │       └── MonitorFilters.tsx          (shared filter bar)
    ├── hooks/
    │   ├── useEquipos.ts                   (F4.1–F4.7)
    │   ├── useEstructura.ts                (F5.1–F5.4)
    │   ├── useEncuentros.ts                (F6.1–F6.6)
    │   ├── useColoquios.ts                 (F7.1–F7.5)
    │   ├── useTareas.ts                    (F8.1–F8.3)
    │   ├── useAvisos.ts                    (FL-09)
    │   └── useMonitorCoordinacion.ts       (F2.7, F2.9)
    ├── services/
    │   ├── equipos.api.ts
    │   ├── estructura.api.ts
    │   ├── encuentros.api.ts
    │   ├── coloquios.api.ts
    │   ├── tareas.api.ts
    │   ├── avisos.api.ts
    │   └── monitor.api.ts
    ├── types/
    │   ├── equipos.types.ts
    │   ├── estructura.types.ts
    │   ├── encuentros.types.ts
    │   ├── coloquios.types.ts
    │   ├── tareas.types.ts
    │   ├── avisos.types.ts
    │   └── monitor.types.ts
    └── pages/
        ├── CoordinacionHome.tsx            (dashboard / landing)
        ├── EquiposPages.tsx (multi-export)  (index, masiva, clonar, etc.)
        ├── EstructuraPages.tsx             (carreras, cohortes, programas, evaluaciones)
        ├── EncuentrosPages.tsx             (list, crear, editar, guardias)
        ├── ColoquiosPages.tsx              (dashboard, crear, detail, admin)
        ├── TareasPages.tsx                 (mis-tareas, asignar, admin)
        ├── AvisosPages.tsx                 (list, crear, editar)
        └── MonitorPages.tsx                (general, auditoria)
```

## Dependencies

- **C-21** (frontend-shell-y-auth): DEPENDENCY — provides routing, layout, sidebar, API client, auth context, permission hooks
- **C-08** (equipos-docentes-api): DEPENDENCY — equipo docente CRUD, asignaciones, clonar, export APIs
- **C-13** (avisos-api): DEPENDENCY — avisos CRUD + publish APIs
- **C-14** (tareas-internas-api): DEPENDENCY — tareas CRUD + workflow APIs
- **C-15** (encuentros-api): DEPENDENCY — encuentros CRUD, recurrente, guardias APIs
- **C-16** (coloquios-api): DEPENDENCY — coloquios CRUD + convocatorias APIs
- **C-22** (frontend-academico-docente): REFERENCE — pattern for hook/service/component organization

## Integration Points (provisional — to confirm with backend API specs)

| Feature | Backend API | Method | Request | Response |
|---------|------------|--------|---------|----------|
| List equipos | `/api/v1/equipos/mis-equipos` | GET | — | `Equipo[]` |
| List asignaciones | `/api/v1/equipos/asignaciones` | GET | filters | `Asignacion[]` |
| Asignación individual | `/api/v1/equipos/asignaciones` | POST | `{ docente_id, materia_id, rol, vigencia }` | `Asignacion` |
| Asignación masiva | `/api/v1/equipos/asignaciones/masiva` | POST | `{ docente_ids[], materia_id, cohorte_id, rol, vigencia }` | `{ count }` |
| Clonar equipo | `/api/v1/equipos/clonar` | POST | `{ origen, destino }` | `{ asignaciones_creadas }` |
| Actualizar vigencia | `/api/v1/equipos/vigencia` | PUT | `{ equipo_id, fecha_desde, fecha_hasta }` | `{ updated_count }` |
| Export equipo | `/api/v1/equipos/export` | GET | `{ equipo_id }` | CSV (file download) |
| ABM carreras | `/api/v1/estructura/carreras` | GET/POST | — / `{ codigo, nombre }` | `Carrera[]` / `Carrera` |
| ABM cohortes | `/api/v1/estructura/cohortes` | GET/POST | — / `{ nombre, year, vigencia }` | `Cohorte[]` / `Cohorte` |
| Programas | `/api/v1/estructura/programas` | GET/POST | — / FormData (file) | `Programa[]` / `Programa` |
| Evaluaciones | `/api/v1/estructura/evaluaciones` | GET/POST | — / `{ materia_id, tipo, fecha }` | `Evaluacion[]` / `Evaluacion` |
| Create recurrente | `/api/v1/encuentros/recurrente` | POST | `{ materia_id, dia, horario, inicio, semanas }` | `{ instancias[] }` |
| Edit encuentro | `/api/v1/encuentros/{id}` | PUT | `{ estado, enlace, grabacion }` | `Encuentro` |
| List encuentros | `/api/v1/encuentros` | GET | filters | `Encuentro[]` |
| Guardias | `/api/v1/encuentros/guardias` | GET/POST | — / `{ tutor_id, fecha, horario }` | `Guardia[]` / `Guardia` |
| Coloquios metrics | `/api/v1/coloquios/metricas` | GET | — | `Metricas` |
| CRUD coloquios | `/api/v1/coloquios` | GET/POST | — / `{ materia_id, fechas, cupos }` | `Convocatoria[]` / `Convocatoria` |
| Import alumnos | `/api/v1/coloquios/importar-alumnos` | POST | FormData | `{ imported_count }` |
| CRUD tareas | `/api/v1/tareas` | GET/POST/PUT | — / `{ asignado_a, materia_id, descripcion }` | `Tarea[]` / `Tarea` |
| Mis tareas | `/api/v1/tareas/mis-tareas` | GET | filters | `Tarea[]` |
| CRUD avisos | `/api/v1/avisos` | GET/POST/PUT | — / `{ titulo, cuerpo, alcance, roles, vigencia }` | `Aviso[]` / `Aviso` |
| Monitor general | `/api/v1/analisis/monitor/general` | GET | filters + date_range | `MonitorEntry[]` |
| Auditoria | `/api/v1/analisis/monitor/auditoria` | GET | filters | `AuditoriaEntry[]` |

## Out of Scope

- **C-22** (frontend-academico-docente): grade import, analysis, per-commission views (PROFESOR module)
- **C-24** (frontend-finanzas-y-admin): liquidaciones, facturas, payroll, tenant user admin
- **Estructura académica full** (C-06 / C-24 boundary): the ABM for carreras/cohortes included here is the COORDINADOR-facing subset; full CRUD with advanced options belongs to C-24
- **Módulo de corrección asistida (IA)**: external module
- **Mensajería interna** (F3.4 / inbox): F3.4 belongs to C-22 or a future change
- **E2E tests**: only component and integration tests with mocks as specified in CHANGES.md
- **WebSocket real-time**: polling via TanStack Query refetchInterval only
- **Dark mode / theme toggling**: not in scope for any frontend change

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| **Large scope (7 sub-modules, 27 features)** | Modular directory structure per domain; can be implemented in parallel sub-tasks. Each épica is self-contained. |
| **Equipos asignación masiva UX complexity** | Use multi-select with search (combobox) + batch selection patterns; progressively disclose bulk options |
| **Encuentros recurrentes: instance generation feedback** | Show inline progress spinner; if generation is slow (>2s), transition to polling with `refetchInterval` |
| **Coloquios: complex form (multiple days + slots)** | Wizard/stepper form: step 1 = metadata, step 2 = days/cupos, step 3 = confirm |
| **Avisos: rich text content** | Lightweight markdown editor (no WYSIWYG library needed — use textarea with markdown preview or a small rich-text component like TipTap if required) |
| **Stale data after mutations** | TanStack Query `onSuccess` invalidates all related query keys; entities use scoped keys per domain |
| **Permission mismatch** | Backend enforces via RBAC; frontend hides nav items and disables actions based on `can()` hook |
| **Large monitoring datasets** | Backend paginates; frontend uses page-based pagination |
| **File upload for programas** | Single file upload per materia×cohorte; max size handled by backend; frontend shows progress bar |
| **Recurrent instance edit vs series edit** | Clear UI separation: "edit this instance" vs "edit all future instances" (recurring event pattern) |

## Estimate

- **~70-85 files** across `features/coordinacion/` (components, hooks, services, types, pages)
- **~6000-8000 lines** (TSX + TS)
- **~40-50 components** (across 7 sub-domains: equipos, estructura, encuentros, coloquios, tareas, avisos, monitor)
- **~7 hooks** (one per API domain)
- **~14 service files** (7 API modules)
- **~7 type files** (one per domain)
- Estimated effort: **8-12 days** for a single frontend developer (or 5-7 with 2 developers working in parallel on separate épicas)
