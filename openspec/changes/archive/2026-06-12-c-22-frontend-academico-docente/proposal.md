# Proposal: C-22 — Frontend Académico Docente

## Intent

Enable the PROFESOR role to manage their commission/class entirely through the SPA: import grades from the LMS, configure thresholds, detect at-risk students, view rankings and final grades, export reports, and send communications — all within a single feature module under `features/comisiones/`. Also covers the TUTOR/PROFESOR monitoring view (F2.8) and, partially, the COORDINADOR general monitoring view (F2.7).

This change consumes three backend feature sets already built: **C-10** (calificaciones + umbral), **C-11** (análisis, atrasados, reportes), and **C-12** (comunicaciones con cola). It builds on the shell established by **C-21**.

## Scope

All features listed below map to functions defined in `knowledge-base/06_funcionalidades.md`:

| # | Funcionalidad | KB Ref | Backend API |
|---|--------------|--------|-------------|
| 1 | Commission selector (materia + cohorte) | — (navigation) | `GET /api/v1/calificaciones/{materia_id}` |
| 2 | Importar calificaciones con preview + selección de actividades | F1.1 | `POST /api/v1/calificaciones/preview`, `POST /api/v1/calificaciones/import` |
| 3 | Importar reporte de finalización de actividades | F1.2 | `POST /api/v1/calificaciones/import-finalizacion` |
| 4 | Configurar umbral de aprobación | F2.1 | `GET/PUT /api/v1/umbral/{materia_id}` |
| 5 | Visualizar alumnos atrasados | F2.2 | `GET /api/analisis/atrasados` |
| 6 | Ranking de actividades aprobadas | F2.3 | `GET /api/analisis/ranking` |
| 7 | Reportes rápidos por materia | F2.4 | `GET /api/analisis/reporte-rapido` |
| 8 | Notas finales agrupadas + export CSV | F2.5 | `GET /api/analisis/notas-finales`, `GET /api/analisis/notas-finales/export` |
| 9 | Detección + export de TPs sin corregir | F2.6 | `GET /api/analisis/tps-sin-corregir/export` |
| 10 | Monitor de seguimiento (tutor/profesor) | F2.8 | `GET /api/analisis/monitor/propio` |
| 11 | Monitor general (coordinación) | F2.7 | `GET /api/analisis/monitor/general` |
| 12 | Preview de comunicación a atrasados | F3.1 | `POST /api/comunicaciones/preview` |
| 13 | Envío masivo + tracking de estado en tiempo real | F3.2 | `POST /api/comunicaciones/lote`, `GET /api/comunicaciones/lote/{lote_id}/estado` |
| 14 | Aprobación/cancelación de lotes | F3.3 | `POST /api/comunicaciones/lote/{lote_id}/aprobar`, `POST /api/comunicaciones/lote/{lote_id}/cancelar`, `POST /api/comunicaciones/{comunicacion_id}/cancelar` |
| 15 | Reintentar comunicación fallida | F3.2 | `POST /api/comunicaciones/{comunicacion_id}/retry` |
| 16 | Vaciar datos de una materia | F1.5 | `POST /api/v1/calificaciones/vaciar` (o endpoint específico de C-10) |

## User Flows (mapping to FL-02)

### Flow A — Import → Analyze → Communicate (FL-02 main path)
1. Teacher logs in → sidebar shows `Comisiones` item (filtered by `can('comisiones:read')`)
2. Teacher selects materia + cohorte via a dropdown/selector on the Comisiones dashboard
3. Uploads CSV/XLSX grades file → `POST /calificaciones/preview` → shows detected activities table
4. Selects which activities to include → `POST /calificaciones/import` → data persisted
5. Configures threshold via `GET/PUT /umbral/{materia_id}` (default 60%)
6. System auto-computes and presents: at-risk students table, ranking, quick reports, final grades
7. Teacher optionally uploads completion report → `POST /calificaciones/import-finalizacion` → cross-references with grades → shows uncorrected submissions → exports CSV
8. Teacher selects at-risk students → `POST /comunicaciones/preview` → sees personalized message preview → confirms → `POST /comunicaciones/lote` → lot enters Pendiente state
9. Real-time tracking via `GET /comunicaciones/lote/{lote_id}/estado` (polling every 5s or TanStack Query refetch)

### Flow B — Quick overview
1. Teacher opens commission → quick report tab shows summary KPIs (total students, approved %, pending %)
2. Ranking tab shows ordered table of students by approved activities
3. Final grades tab shows calculated grades with export button → triggers file download

### Flow C — Monitoring (TUTOR / PROFESOR)
1. Monitor tab shows filterable table: by student name, email, comision, regional, activity
2. COORDINADOR has same view with additional date-range filter and cross-commission scope (F2.7)

## State & UI per Feature

### Commission Selector
- **State**: list of materia+cohorte pairs from user session via `/api/auth/me` (already available in AuthContext) or explicit fetch
- **UI**: combo box with materia + cohorte; once selected, all subsequent API calls use `{materia_id}`

### Grade Import (F1.1, F1.2)
- **Steps**: file upload → preview table with checkboxes per activity → confirm import
- **States**: idle → uploading → previewing → importing → success/error
- **Error handling**: invalid file format, missing columns, duplicate data, server validation errors

### Threshold (F2.1)
- **State**: current threshold value (cached from GET), editable via PUT
- **UI**: number input with slider, percentage display, save button

### At-risk Students (F2.2)
- **State**: array of `{alumno, actividades_faltantes, nota_promedio, estado}`
- **UI**: sortable table with filter by student name; checkbox per row for communication targeting
- **Polling**: none (static after import, refreshed on manual action)

### Ranking (F2.3)
- **State**: ordered array of `{alumno, actividades_aprobadas, total_actividades}`
- **UI**: table sorted descending by approved count

### Quick Reports (F2.4)
- **State**: summary KPIs object
- **UI**: card grid with metrics + empty state when no data

### Final Grades (F2.5)
- **State**: array of `{alumno, nota_final, estado}`
- **UI**: table + export button (triggers CSV download via direct link or blob)

### TP Detection (F2.6)
- **UI**: results table + export button pointing to `/api/analisis/tps-sin-corregir/export`

### Monitoring (F2.7, F2.8)
- **State**: filtered query results
- **UI**: filter bar + data table; filters include student name, email, comision, regional, activity, min activity completion
- **Extra for COORDINADOR**: date range filter

### Communication (F3.1, F3.2, F3.3, F3.4)
- **Preview**: modal/drawer showing subject + body as recipient would see it
- **Batch send**: confirm button triggers POST; returns lote_id
- **Tracking**: polling or WebSocket on lote state; state machine badge per message
- **Actions per lote**: approve, cancel (for approver role), retry (for failed)

### Clear Data (F1.5)
- **UI**: confirmation dialog ("¿Estás seguro? Esta acción no se puede deshacer") → POST → success toast → refresh commission state

## Architecture

### Routing

```tsx
// Added to App.tsx under <Route element={<Layout />}>
<Route path="/comisiones" element={<ComisionesLayout />}>
  <Route index element={<ComisionSelector />} />
  <Route path=":materiaId" element={<ComisionDashboard />}>
    <Route index element={<ResumenTab />} />
    <Route path="importar" element={<ImportarTab />} />
    <Route path="umbral" element={<UmbralTab />} />
    <Route path="atrasados" element={<AtrasadosTab />} />
    <Route path="ranking" element={<RankingTab />} />
    <Route path="reportes" element={<ReportesTab />} />
    <Route path="notas-finales" element={<NotasFinalesTab />} />
    <Route path="tps-sin-corregir" element={<TpsSinCorregirTab />} />
    <Route path="monitor" element={<MonitorTab />} />
    <Route path="comunicaciones" element={<ComunicacionesTab />} />
  </Route>
</Route>
```

### Navigation
- Sidebar gets a new entry: `{ label: 'Comisiones', path: '/comisiones', icon: LayoutGrid, permission: 'comisiones:read' }`
- Within commission dashboard, a sub-navigation (tabs or side nav) switches between feature tabs

### Data Flow
- All data fetching via TanStack Query hooks with `queryKey` scoped by `materiaId`
- Mutations via `useMutation` with `onSuccess` invalidation of related queries
- File upload via FormData through Axios (no custom upload component needed — native `<input type="file">`)
- Communication tracking via polling (useQuery with `refetchInterval: 5000`) on active/completed actions
- CSV exports via direct window.open or download blob from Axios response

### State per Session
- `materiaId` selected persists in URL param (shareable, back-button safe)
- Current threshold is cached server-side and refetched; optimistic updates on save
- Communication lotes polled only while a lote is in non-terminal state (Pendiente/Enviando)

## Directory Structure

```
frontend/src/features/
└── comisiones/
    ├── components/
    │   ├── ComisionSelector.tsx         (materia + cohorte dropdown)
    │   ├── ComisionDashboard.tsx        (tabs layout)
    │   ├── GradeUploader.tsx            (file input + preview table)
    │   ├── ActivitySelector.tsx         (checkbox list for preview)
    │   ├── ThresholdEditor.tsx          (slider + save)
    │   ├── AtrasadosTable.tsx           (sortable table + selection)
    │   ├── RankingTable.tsx
    │   ├── ReportesSummary.tsx          (KPI cards)
    │   ├── NotasFinalesTable.tsx        + ExportButton
    │   ├── TpsSinCorregirTable.tsx      + ExportButton
    │   ├── MonitorTable.tsx             (filters + data)
    │   ├── MonitorFilters.tsx
    │   ├── ComunicacionPreview.tsx      (modal)
    │   ├── ComunicacionTracking.tsx     (lote state badges)
    │   ├── LoteActions.tsx              (approve/cancel/retry)
    │   └── ClearDataDialog.tsx
    ├── hooks/
    │   ├── useCalificaciones.ts         (preview, import, import-finalizacion)
    │   ├── useUmbral.ts                 (GET, PUT)
    │   ├── useAtrasados.ts
    │   ├── useRanking.ts
    │   ├── useReporteRapido.ts
    │   ├── useNotasFinales.ts
    │   ├── useMonitor.ts
    │   ├── useComunicaciones.ts         (preview, send, status, approve, cancel, retry)
    │   └── useClearData.ts
    ├── services/
    │   └── comisiones.api.ts            (all API calls)
    ├── types/
    │   └── comisiones.types.ts          (domain types)
    └── pages/
        ├── ComisionesPage.tsx           (list/selector)
        └── ComisionDetailPage.tsx       (tabs container)
```

## Dependencies

- **C-21** (frontend-shell-y-auth): COMPLETED [x] — provides routing, layout, sidebar, API client, auth context, permission hooks
- **C-10** (calificaciones-y-umbral): COMPLETED [x] — grade import preview + import + threshold APIs
- **C-11** (analisis-atrasados-reportes): COMPLETED [x] — at-risk, ranking, reports, monitoring APIs
- **C-12** (comunicaciones-cola-worker): COMPLETED [x] — communication preview, batch send, tracking, approval APIs

## Integration Points

| Feature | Backend API | Method | Request | Response |
|---------|------------|--------|---------|----------|
| Grade preview | `/api/v1/calificaciones/preview` | POST | FormData (file) | `{ actividades: Activity[], alumnos: Alumno[] }` |
| Grade import | `/api/v1/calificaciones/import` | POST | `{ materia_id, activities_selected[] }` | `{ imported_count, errors[] }` |
| Finalizacion import | `/api/v1/calificaciones/import-finalizacion` | POST | FormData (file) | `{ sin_corregir: Submission[] }` |
| Get threshold | `/api/v1/umbral/{materia_id}` | GET | — | `{ umbral: number }` |
| Update threshold | `/api/v1/umbral/{materia_id}` | PUT | `{ umbral: number }` | `{ umbral: number }` |
| At-risk students | `/api/analisis/atrasados` | GET | `{ materia_id }` | `Atrasado[]` |
| Ranking | `/api/analisis/ranking` | GET | `{ materia_id }` | `RankingEntry[]` |
| Quick report | `/api/analisis/reporte-rapido` | GET | `{ materia_id }` | `ReporteRapido` |
| Final grades | `/api/analisis/notas-finales` | GET | `{ materia_id }` | `NotaFinal[]` |
| Export final grades | `/api/analisis/notas-finales/export` | GET | `{ materia_id }` | CSV (file download) |
| Export TPs sin corregir | `/api/analisis/tps-sin-corregir/export` | GET | `{ materia_id }` | CSV (file download) |
| Monitor propio | `/api/analisis/monitor/propio` | GET | filters | `MonitorEntry[]` |
| Monitor general | `/api/analisis/monitor/general` | GET | filters + date_range | `MonitorEntry[]` |
| Comms preview | `/api/comunicaciones/preview` | POST | `{ materia_id, alumno_ids[] }` | `{ asunto, cuerpo }` |
| Batch send | `/api/comunicaciones/lote` | POST | `{ materia_id, alumno_ids[], asunto, cuerpo }` | `{ lote_id }` |
| Lote status | `/api/comunicaciones/lote/{lote_id}/estado` | GET | — | `{ estado, items: ComunicacionItem[] }` |
| Approve lote | `/api/comunicaciones/lote/{lote_id}/aprobar` | POST | — | `{ success }` |
| Cancel lote | `/api/comunicaciones/lote/{lote_id}/cancelar` | POST | — | `{ success }` |
| Cancel single | `/api/comunicaciones/{comunicacion_id}/cancelar` | POST | — | `{ success }` |
| Retry | `/api/comunicaciones/{comunicacion_id}/retry` | POST | — | `{ success }` |
| Clear data | `/api/v1/calificaciones/vaciar` (assumed) | POST | `{ materia_id }` | `{ success }` |

## Out of Scope

- **C-23** (frontend-coordinacion): equipo docente management, avisos, tareas internas, encuentros, coloquios
- **C-24** (frontend-finanzas-y-admin): liquidaciones, facturas, estructura académica admin, auditoría
- **Módulo de corrección asistida (IA)**: external module, not part of this SPA
- **Mensajería interna** (F3.4 / inbox): belongs to C-23 or a future change
- **E2E tests**: only component and integration tests with mocks as specified in CHANGES.md
- **WebSocket real-time**: communication tracking via polling only; WebSocket upgrades considered technical debt for a future change
- **Dark mode / theme toggling**: not in scope for any frontend change

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| **Large CSV/XLSX files** (thousands of rows) causing UI freezes | Backend handles parsing and returns structured JSON; frontend only renders the response. If preview response is large, virtualize the table. |
| **Race condition on concurrent imports** | Backend owns locking per materia_id; frontend disables import button while a request is in-flight |
| **File format errors not detectable on frontend** | Backend validates and returns structured error messages per row; frontend displays them in an inline alert or per-row badge |
| **Stale data after import** | `onSuccess` of import mutation invalidates all `['analisis', materiaId]` queries; TanStack Query auto-refetches |
| **Polling overhead for communication tracking** | Poll only while lotes are in non-terminal state (check via `lote.estado`); stop polling when all terminal |
| **Large monitoring datasets** | Backend paginates; frontend uses infinite query or page-based pagination |
| **User navigates away during import** | TanStack Query keeps the mutation promise; no state loss on re-mount |
| **Permission mismatch** (teacher accesses another's commission) | Backend enforces via RBAC; frontend pre-filters visible commissions from session data; 403 on API call is caught and shown as error |
| **CSV download browser compatibility** | Use Axios blob response + URL.createObjectURL + temporary anchor click; works in all modern browsers |
| **Export for >10k rows** | Backend streams the file; frontend shows spinner until download starts |

## Estimate

- **~35-40 files** across `features/comisiones/` (components, hooks, services, types, pages)
- **~3000-4000 lines** (TSX + TS)
- **~20-25 components** (including tables, modals, forms, filter bars)
- **~10 hooks** (one per feature group)
- Estimated effort: **3-5 days** for a single frontend developer
