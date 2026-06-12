# Tasks: C-22 — Frontend Académico Docente

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1720 |
| New files | 40 |
| Modified files | 1 (App.tsx) |

## Phase 1: Foundation — Types + API Service

### Task T-1.1: Create domain types

- **File**: `frontend/src/features/comisiones/types/comisiones.types.ts`
- Create all TypeScript interfaces from design §4:
  - `MateriaCohorte` — commission (materia + cohorte) pair
  - `ActivityDTO`, `AlumnoPreviewDTO`, `ImportPreviewResponse` — grade import preview
  - `ImportConfirmRequest`, `ImportError`, `ImportConfirmResponse` — grade import confirm
  - `Umbral` — threshold value
  - `Atrasado`, `RankingEntry`, `ReporteRapido`, `NotaFinal`, `TpsSinCorregirEntry` — analytics
  - `MonitorFilters`, `MonitorEntry` — monitoring
  - `ComunicacionPreviewRequest`, `ComunicacionPreview`, `ComunicacionEnviarRequest`, `ComunicacionEnviarResponse` — communication preview/send
  - `ComunicacionItem`, `ComunicacionLote`, `LoteActionResponse` — communication tracking
  - `ClearDataResponse` — clear data result
- [ ] All types at 120 LOC with `extra='forbid'` convention not applicable (this is TS, not Pydantic)
- [ ] Prefixed `DTO` where backend response differs from request shape
- [ ] Exported for use across the feature module

### Task T-1.2: Create API service layer

- **File**: `frontend/src/features/comisiones/services/comisiones.api.ts`
- Import from `@/shared/services/api` (the shared axios instance)
- Implement all functions matching the integration points table in proposal §Integration Points:
  - [ ] `getMisComisiones(): Promise<MateriaCohote[]>` — commission list
  - [ ] `importPreview(formData: FormData): Promise<ImportPreviewResponse>` — POST to `/api/v1/calificaciones/preview`
  - [ ] `importConfirm(data: ImportConfirmRequest): Promise<ImportConfirmResponse>` — POST to `/api/v1/calificaciones/import`
  - [ ] `importFinalizacion(formData: FormData): Promise<{ sin_corregir: TpsSinCorregirEntry[] }>` — POST to `/api/v1/calificaciones/import-finalizacion`
  - [ ] `getUmbral(materiaId: string): Promise<Umbral>` — GET `/api/v1/umbral/{materiaId}`
  - [ ] `updateUmbral(materiaId: string, data: Umbral): Promise<Umbral>` — PUT `/api/v1/umbral/{materiaId}`
  - [ ] `getAtrasados(materiaId: string): Promise<Atrasado[]>` — GET `/api/analisis/atrasados?materia_id=...`
  - [ ] `getRanking(materiaId: string): Promise<RankingEntry[]>` — GET `/api/analisis/ranking?materia_id=...`
  - [ ] `getReporteRapido(materiaId: string): Promise<ReporteRapido>` — GET `/api/analisis/reporte-rapido?materia_id=...`
  - [ ] `getNotasFinales(materiaId: string): Promise<NotaFinal[]>` — GET `/api/analisis/notas-finales?materia_id=...`
  - [ ] `getNotasFinalesExportUrl(materiaId: string): string` — returns the export URL string for direct download
  - [ ] `getTpsSinCorregir(materiaId: string): Promise<TpsSinCorregirEntry[]>` — GET `/api/analisis/tps-sin-corregir?materia_id=...`
  - [ ] `getTpsSinCorregirExportUrl(materiaId: string): string` — returns the export URL string
  - [ ] `getMonitor(materiaId: string, filters: MonitorFilters, page: number): Promise<{ data: MonitorEntry[], total: number, page: number, total_pages: number }>` — GET `/api/analisis/monitor/propio` or `/general`
  - [ ] `previewComunicacion(data: ComunicacionPreviewRequest): Promise<ComunicacionPreview>` — POST `/api/comunicaciones/preview`
  - [ ] `enviarComunicacion(data: ComunicacionEnviarRequest): Promise<ComunicacionEnviarResponse>` — POST `/api/comunicaciones/lote`
  - [ ] `getLoteStatus(loteId: string): Promise<ComunicacionLote>` — GET `/api/comunicaciones/lote/{loteId}/estado`
  - [ ] `loteAction(loteId: string, action: 'approve' | 'cancel' | 'retry', comunicacionId?: string): Promise<LoteActionResponse>`
  - [ ] `clearData(materiaId: string): Promise<{ success: boolean }>` — POST `/api/v1/calificaciones/vaciar`
- [ ] File at ~100 LOC, following same pattern as `auth.api.ts` (async functions using `api` instance)
- [ ] All functions typed with proper request/response types from `comisiones.types.ts`
- [ ] Export URLs for CSV exports are string getters, not async functions

---

## Phase 2: Pages + Routing

### Task T-2.1: Create ComisionesPage (entry point)

- **File**: `frontend/src/features/comisiones/pages/ComisionesPage.tsx`
- [ ] Wrap in `PermissionGuard` with permission `comisiones:read`
- [ ] On mount, if user has exactly 1 commission, redirect to `/comisiones/{materiaId}`
- [ ] If multiple commissions, render `<ComisionSelector />`
- [ ] If none, show "No tenés comisiones asignadas" (REQ-GI-01 Scenario 2)
- [ ] Loading state: centered spinner while session resolves (REQ-GI-01 Scenario 4)

### Task T-2.2: Create ComisionDetailPage (tabs container)

- **File**: `frontend/src/features/comisiones/pages/ComisionDetailPage.tsx`
- [ ] Get `materiaId` from `useParams()`
- [ ] Render `<TabNav />` with active tab highlighted
- [ ] Render `<Outlet />` for tab content
- [ ] Pass `materiaId` to all child tab components via prop or context
- [ ] Read-only if commission has no imported data yet (tabs except Importar disabled)

### Task T-2.3: Create TabNav component

- **File**: `frontend/src/features/comisiones/components/TabNav.tsx`
- [ ] Horizontal tab bar rendered as `<NavLink>` elements
- [ ] Tabs: Resumen, Importar, Umbral, Atrasados, Ranking, Notas Finales, TPs sin corregir, Monitor, Comunicaciones
- [ ] Active tab determined by `location.pathname` matching tab path
- [ ] Styled consistently with Tailwind (underline or pill style per design system)

### Task T-2.4: Update App.tsx with comisiones routes

- **File**: `frontend/src/App.tsx`
- [ ] Add imports for `ComisionesPage` and `ComisionDetailPage`
- [ ] Insert route block inside ` <Route element={<Layout />}>` after the `/` route:
  ```tsx
  <Route path="/comisiones" element={<ComisionesPage />} />
  <Route path="/comisiones/:materiaId" element={<ComisionDetailPage />}>
    <Route index element={<ResumenTab />} />
    <Route path="importar" element={<ImportarTab />} />
    <Route path="umbral" element={<UmbralTab />} />
    <Route path="atrasados" element={<AtrasadosTab />} />
    <Route path="ranking" element={<RankingTab />} />
    <Route path="notas-finales" element={<NotasFinalesTab />} />
    <Route path="tps-sin-corregir" element={<TpsSinCorregirTab />} />
    <Route path="monitor" element={<MonitorTab />} />
    <Route path="comunicaciones" element={<ComunicacionesTab />} />
  </Route>
  ```
- [ ] Verify that the sidebar entry `{ label: 'Comisiones', path: '/comisiones', icon: LayoutGrid, permission: 'comisiones:read' }` exists in `Sidebar.tsx`

---

## Phase 3: Commission Selector

### Task T-3.1: Create useComisiones hook

- **File**: `frontend/src/features/comisiones/hooks/useComisiones.ts`
- [ ] `useComisiones()` returns `useQuery<MateriaCohorte[]>` with `queryKey: ['comisiones', 'materias']`
- [ ] Calls `comisionesApi.getMisComisiones()` as queryFn
- [ ] `staleTime: 5 * 60 * 1000` (cache for 5 minutes)
- [ ] `enabled: !!getAccessToken()`

### Task T-3.2: Create ComisionSelector component

- **File**: `frontend/src/features/comisiones/components/ComisionSelector.tsx`
- [ ] Uses `useComisiones()` to fetch available commissions
- [ ] Renders a dropdown/combobox with format `"{materia_nombre} — {cohorte_nombre}"`
- [ ] Shows placeholder "Seleccioná una comisión para empezar" (REQ-GI-01 Scenario 1)
- [ ] On selection, navigates to `/comisiones/{materiaId}` (REQ-GI-01 Scenario 3)
- [ ] Loading state: spinner while fetching (REQ-GI-01 Scenario 4)
- [ ] Empty state: "No tenés comisiones asignadas" with disabled selector (REQ-GI-01 Scenario 2)
- [ ] Handles navigation via `useNavigate()`

---

## Phase 4: Threshold

### Task T-4.1: Create useUmbral hook

- **File**: `frontend/src/features/comisiones/hooks/useUmbral.ts`
- [ ] `useUmbral(materiaId)` — `useQuery<Umbral>` with `queryKey: ['umbral', materiaId]`, calls `comisionesApi.getUmbral(materiaId)`, `enabled: !!materiaId`
- [ ] `useUmbralMutation(materiaId)` — `useMutation` calling `comisionesApi.updateUmbral(materiaId, ...)`, on success invalidates `['umbral', materiaId]`

### Task T-4.2: Create ThresholdEditor component

- **File**: `frontend/src/features/comisiones/components/ThresholdEditor.tsx`
- [ ] Slider + number input displaying percentage 0–100 (REQ-AN-01 Scenario 1)
- [ ] Local state tracks current value; compare with original to enable/disable "Guardar" (REQ-AN-01 Scenario 2)
- [ ] "Cancelar" button reverts to original value (REQ-AN-01 Scenario 5)
- [ ] Calls `useUmbralMutation` on save (REQ-AN-01 Scenario 3)
- [ ] Toast on success: "Umbral actualizado a {value}%" (REQ-AN-01 Scenario 3)
- [ ] Error handling: toast + keep edited value (REQ-AN-01 Scenario 4)
- [ ] Loading: skeleton/shimmer while GET is in flight (REQ-AN-01 Scenario 6)
- [ ] Error loading: message + "Reintentar" button (REQ-AN-01 Scenario 7)

### Task T-4.3: Create UmbralTab component

- **File**: `frontend/src/features/comisiones/components/UmbralTab.tsx`
- [ ] Wraps `<ThresholdEditor materiaId={...} />`
- [ ] Receives `materiaId` as prop
- [ ] Thin wrapper (~15 LOC), delegates all logic to ThresholdEditor

---

## Phase 5: Grade Import Flow

### Task T-5.1: Create useCalificaciones hook

- **File**: `frontend/src/features/comisiones/hooks/useCalificaciones.ts`
- [ ] `useImportPreview()` — `useMutation` accepting `File`, builds `FormData`, calls `comisionesApi.importPreview(formData)`
- [ ] `useImportConfirm(materiaId)` — `useMutation` accepting `string[]` (activity IDs), calls `comisionesApi.importConfirm(...)`, on success invalidates all `['analisis', materiaId]` queries
- [ ] `useImportFinalizacion(materiaId)` — `useMutation` accepting `File`, builds `FormData`, calls `comisionesApi.importFinalizacion(formData)`, on success invalidates `['analisis', materiaId, 'tps-sin-corregir']`

### Task T-5.2: Create GradeUploader component

- **File**: `frontend/src/features/comisiones/components/GradeUploader.tsx`
- [ ] File input accepting `.csv,.xlsx` (REQ-GI-02 Scenario 1)
- [ ] Client-side file type validation: reject non-.csv/.xlsx with inline error (REQ-GI-02 Scenario 2)
- [ ] Uses `useImportPreview()` mutation
- [ ] States: idle → uploading (spinner + disabled input) → preview (calls `onPreview` callback) → error (REQ-GI-03 Scenarios 1–4)
- [ ] Loading: "Procesando archivo..." text with spinner (REQ-GI-03 Scenario 4)
- [ ] Backend validation errors: inline alert with message (REQ-GI-03 Scenario 2)
- [ ] Network errors: "Error de conexión..." message (REQ-GI-03 Scenario 3)
- [ ] Resets input value after upload so same file can be re-selected

### Task T-5.3: Create ActivitySelector component

- **File**: `frontend/src/features/comisiones/components/ActivitySelector.tsx`
- [ ] Receives `ImportPreviewResponse` with activities and alumnos
- [ ] Table with columns: checkbox, activity name, type, sample values (first 3 rows) (REQ-GI-03 Scenario 1)
- [ ] All checkboxes checked by default (REQ-GI-04 Scenario 1)
- [ ] Summary: "Se detectaron {N} actividades y {M} alumnos" (REQ-GI-03 Scenario 1)
- [ ] "Confirmar importación" and "Volver" buttons (REQ-GI-03 Scenario 1)
- [ ] Disable "Confirmar importación" if no activities checked, show "Seleccioná al menos una actividad" (REQ-GI-04 Scenario 6)
- [ ] On confirm: calls `useImportConfirm()` mutation
- [ ] Success state: "{imported_count} calificaciones importadas correctamente" with "Ver análisis" and "Importar más datos" buttons (REQ-GI-04 Scenario 3)
- [ ] Partial errors: expandable error list (REQ-GI-04 Scenario 4)
- [ ] Import failure: "Reintentar" button, keep preview visible (REQ-GI-04 Scenario 5)

### Task T-5.4: Create ImportarTab component

- **File**: `frontend/src/features/comisiones/components/ImportarTab.tsx`
- [ ] Orchestrates GradeUploader → ActivitySelector flow
- [ ] Manages state machine: idle → uploading → previewing → importing → success/error (design §6)
- [ ] Also handles completion report upload for uncorrected TP detection (REQ-GI-05)
- [ ] Shows results of uncorrected TP detection: table + count + export button (REQ-GI-05 Scenario 1)
- [ ] Empty uncorrected TP state: "No se detectaron entregas sin corregir" with disabled export (REQ-GI-05 Scenario 2)

---

## Phase 6: Analysis Views (Parallel)

### Task T-6.1: Create analysis hooks (atrasados, ranking, reporte, notas, tps)

- **Files**:
  - `frontend/src/features/comisiones/hooks/useAtrasados.ts`
  - `frontend/src/features/comisiones/hooks/useRanking.ts`
  - `frontend/src/features/comisiones/hooks/useReporteRapido.ts`
  - `frontend/src/features/comisiones/hooks/useNotasFinales.ts`
  - `frontend/src/features/comisiones/hooks/useTpsSinCorregir.ts`
- [ ] Each hook follows the same pattern: `useQuery<T>` with `queryKey: ['analisis', materiaId, '<slug>']`, `enabled: !!materiaId`
- [ ] Each calls the corresponding `comisionesApi.*` function
- [ ] `useNotasFinales` also exports a utility for CSV download via `window.open(exportUrl, '_blank')`

### Task T-6.2: Create AtrasadosTable component

- **File**: `frontend/src/features/comisiones/components/AtrasadosTable.tsx`
- [ ] Sortable table: columns = checkbox, Alumno, Email, Actividades faltantes, Nota promedio, Estado (REQ-AN-02 Scenario 1)
- [ ] Sortable by clicking column headers (asc/desc toggle) (REQ-AN-02 Scenario 1)
- [ ] Count above table: "Se detectaron {N} alumnos atrasados" (REQ-AN-02 Scenario 1)
- [ ] Per-row checkbox for selection (REQ-AN-02 Scenario 3)
- [ ] Header checkbox for select all / deselect all (REQ-AN-02 Scenarios 4–5)
- [ ] Floating action bar: "Comunicar seleccionados ({count})" (REQ-AN-02 Scenario 3)
- [ ] Search input to filter by student name (client-side, case-insensitive) (REQ-AN-02 Scenario 8)
- [ ] Empty state: "No hay alumnos atrasados en esta comisión" with success icon (REQ-AN-02 Scenario 2)
- [ ] Loading: skeleton table with 5 placeholder rows (REQ-AN-02 Scenario 6)
- [ ] Error: message + "Reintentar" (REQ-AN-02 Scenario 7)
- [ ] Exposes `selectedAlumnoIds: string[]` to parent for communication flow

### Task T-6.3: Create RankingTable component

- **File**: `frontend/src/features/comisiones/components/RankingTable.tsx`
- [ ] Columns: Posición, Alumno, Actividades aprobadas, Total actividades, Porcentaje (REQ-AN-03 Scenario 1)
- [ ] Ordered by approved count descending (REQ-AN-03 Scenario 1)
- [ ] Top 3 positions: gold/silver/bronze visual styling (REQ-AN-03 Scenario 1)
- [ ] Empty state: "No hay actividades importadas para mostrar ranking" + link to import tab (REQ-AN-03 Scenario 2)
- [ ] Loading: skeleton table (REQ-AN-03 Scenario 3)
- [ ] Error: message + "Reintentar" (REQ-AN-03 Scenario 4)

### Task T-6.4: Create ReportesSummary component

- **File**: `frontend/src/features/comisiones/components/ReportesSummary.tsx`
- [ ] KPI card grid: Total alumnos, Con al menos una aprobada, Atrasados (warning icon > 0), Porcentaje de aprobación (color-coded: green ≥ 70%, yellow ≥ 40%, red < 40%) (REQ-AN-04 Scenario 1)
- [ ] Empty state: "No hay datos de esta comisión. Importá calificaciones para ver reportes." (REQ-AN-04 Scenario 2)
- [ ] Loading: 4 skeleton cards (REQ-AN-04 Scenario 3)
- [ ] Error: message + "Reintentar" (REQ-AN-04 Scenario 4)

### Task T-6.5: Create NotasFinalesTable component

- **File**: `frontend/src/features/comisiones/components/NotasFinalesTable.tsx`
- [ ] Columns: Alumno, Email, Nota final (2 decimal places), Estado (Aprobado green / Desaprobado red) (REQ-AN-05 Scenario 1)
- [ ] "Exportar CSV" button triggers download via `window.open()` (REQ-AN-05 Scenario 2)
- [ ] Empty state: "No hay notas finales para mostrar. Importá calificaciones primero." + disabled export (REQ-AN-05 Scenario 3)
- [ ] Loading: skeleton table + spinner on export button (REQ-AN-05 Scenario 4)
- [ ] Error: message + "Reintentar" (REQ-AN-05 Scenario 5)
- [ ] Export failure: error toast (REQ-AN-05 Scenario 6)

### Task T-6.6: Create ExportButton component

- **File**: `frontend/src/features/comisiones/components/ExportButton.tsx`
- [ ] Receives `exportUrl: string` and `disabled: boolean`
- [ ] On click: opens URL in new tab (or Axios blob download for POST-based exports)
- [ ] Shows "Descarga iniciada" toast on click (REQ-AN-05 Scenario 2)
- [ ] Disabled state with tooltip "Sin datos para exportar" (REQ-AN-05 Scenario 3)

### Task T-6.7: Create TpsSinCorregirTable component

- **File**: `frontend/src/features/comisiones/components/TpsSinCorregirTable.tsx`
- [ ] Columns: Alumno, Email, Actividad, Fecha de finalización (REQ-AN-06 Scenario 1)
- [ ] Count: "Se detectaron {N} entregas sin corregir" (REQ-AN-06 Scenario 1)
- [ ] Export CSV button (REQ-AN-06 Scenario 1)
- [ ] Empty state: "No hay trabajos prácticos sin corregir" (REQ-AN-06 Scenario 2)
- [ ] Loading: skeleton table (REQ-AN-06 Scenario 3)
- [ ] Error: message + "Reintentar" (REQ-AN-06 Scenario 4)
- [ ] Export: triggers CSV download + toast (REQ-AN-06 Scenario 5)

### Task T-6.8: Create ResumenTab component

- **File**: `frontend/src/features/comisiones/components/ResumenTab.tsx`
- [ ] Wraps `<ReportesSummary materiaId={...} />`
- [ ] Thin wrapper, delegates to ReportesSummary

### Task T-6.9: Create AtrasadosTab component

- **File**: `frontend/src/features/comisiones/components/AtrasadosTab.tsx`
- [ ] Wraps `<AtrasadosTable />` and manages selection state
- [ ] On "Comunicar seleccionados" click, opens `<ComunicacionPreview />` modal
- [ ] Passes selected `alumno_ids` to the preview/send flow

### Task T-6.10: Create RankingTab component

- **File**: `frontend/src/features/comisiones/components/RankingTab.tsx`
- [ ] Wraps `<RankingTable materiaId={...} />`

### Task T-6.11: Create NotasFinalesTab component

- **File**: `frontend/src/features/comisiones/components/NotasFinalesTab.tsx`
- [ ] Wraps `<NotasFinalesTable materiaId={...} />` + `<ExportButton exportUrl={...} />`

### Task T-6.12: Create TpsSinCorregirTab component

- **File**: `frontend/src/features/comisiones/components/TpsSinCorregirTab.tsx`
- [ ] Wraps `<TpsSinCorregirTable materiaId={...} />` + `<ExportButton exportUrl={...} />`

---

## Phase 7: Monitoring

### Task T-7.1: Create useMonitor hook

- **File**: `frontend/src/features/comisiones/hooks/useMonitor.ts`
- [ ] `useMonitor(materiaId, filters, page)` — `useQuery` with `queryKey: ['analisis', materiaId, 'monitor', filters, page]`
- [ ] Calls `comisionesApi.getMonitor(materiaId, filters, page)`
- [ ] `enabled: !!materiaId`
- [ ] Filters are debounced at 300ms in the component before being passed to the hook

### Task T-7.2: Create MonitorFilters component

- **File**: `frontend/src/features/comisiones/components/MonitorFilters.tsx`
- [ ] Filter inputs: text (nombre, email), dropdown (comision, regional, actividad), number (min actividades completadas) (REQ-MO-01 Scenarios 3–8)
- [ ] Debounce text inputs at 300ms before triggering API call (design §5)
- [ ] "Limpiar filtros" button resets all filters and pagination to page 1 (REQ-MO-01 Scenario 9)
- [ ] For COORDINADOR: additional date range inputs "Fecha desde" / "Fecha hasta" (REQ-MO-02 Scenario 1)
- [ ] Date range validation: "desde" must be before "hasta" (REQ-MO-02 Scenario 3)
- [ ] All filters combined in a single request as query params (REQ-MO-01 Scenario 8)
- [ ] Emits `onFiltersChange(filters)` callback

### Task T-7.3: Create MonitorTable component

- **File**: `frontend/src/features/comisiones/components/MonitorTable.tsx`
- [ ] Columns: Alumno, Email, Comisión, Regional, Actividad, Estado, Última actividad (REQ-MO-01 Scenario 1)
- [ ] Paginated: page size 50, API-returned total + page count drives pagination controls (REQ-MO-01 Scenario 1, REQ-MO-03 Scenarios 1–2)
- [ ] Pagination: "Página {page} de {total_pages}", "Anterior" / "Siguiente" buttons, records summary "Mostrando {from}-{to} de {total} registros" (REQ-MO-01 Scenario 1)
- [ ] Pagination resets to page 1 when filters change (REQ-MO-03 Scenario 4)
- [ ] Empty state: "No se encontraron alumnos para los filtros seleccionados" (REQ-MO-01 Scenario 2)
- [ ] Loading: skeleton table with placeholder rows, pagination hidden, filters disabled (REQ-MO-01 Scenario 12)
- [ ] Error: message + "Reintentar" button, previous data visible below error (REQ-MO-01 Scenario 13)
- [ ] COORDINADOR view uses `/general` endpoint, sees all commissions in tenant (REQ-MO-02 Scenario 5)

### Task T-7.4: Create MonitorTab component

- **File**: `frontend/src/features/comisiones/components/MonitorTab.tsx`
- [ ] Wraps `<MonitorFilters />` + `<MonitorTable />`
- [ ] Manages filter state and page state
- [ ] Passes debounced filters and page to `useMonitor()`

---

## Phase 8: Communications

### Task T-8.1: Create useComunicaciones hook

- **File**: `frontend/src/features/comisiones/hooks/useComunicaciones.ts`
- [ ] `useComunicacionPreview()` — `useMutation` calling `comisionesApi.previewComunicacion(data)`
- [ ] `useComunicacionEnviar()` — `useMutation` calling `comisionesApi.enviarComunicacion(data)`
- [ ] `useComunicacionEstado(loteId)` — `useQuery` with polling: `refetchInterval` returns `5000` if lote is `pendiente`/`enviando`, `false` if `completado`/`cancelado` (REQ-CO-03 Scenario 1–3)
- [ ] `useComunicacionAction(loteId, comunicacionId?)` — `useMutation` dispatching approve/cancel/retry, on success invalidates `['comunicaciones', 'lote', loteId]`

### Task T-8.2: Create ComunicacionPreview component (modal)

- **File**: `frontend/src/features/comisiones/components/ComunicacionPreview.tsx`
- [ ] Modal/drawer showing subject + body as recipient sees it (REQ-CO-01 Scenario 1)
- [ ] Summary: "Se enviará a {N} destinatarios" (REQ-CO-01 Scenario 1)
- [ ] "Enviar a {N} destinatarios", "Cancelar", "Editar" buttons (REQ-CO-01 Scenario 1)
- [ ] Edit mode: subject and body become editable text fields (REQ-CO-01 Scenario 4)
- [ ] Loading state: spinner + "Generando previsualización..." (REQ-CO-01 Scenario 3)
- [ ] Error state: "Error al generar la previsualización" + "Reintentar" (REQ-CO-01 Scenario 2)
- [ ] On "Enviar": calls `useComunicacionEnviar()`, on success transitions to tracking (REQ-CO-02 Scenario 1)
- [ ] Sending loading: spinner on button + "Enviando comunicación..." (REQ-CO-02 Scenario 3)
- [ ] Send failure: toast + modal stays open for retry (REQ-CO-02 Scenario 2)
- [ ] Cancel closes modal, keeps student selection intact (REQ-CO-01 Scenario 5)

### Task T-8.3: Create ComunicacionTracking component

- **File**: `frontend/src/features/comisiones/components/ComunicacionTracking.tsx`
- [ ] Receives `loteId`, uses `useComunicacionEstado(loteId)` for polling (REQ-CO-03)
- [ ] Header: "Estado: {estado}" with color-coded badge (gray Pendiente, blue Enviando, green Enviado, mixed Completado, orange Cancelado) (REQ-CO-06 Scenarios 1–5)
- [ ] Progress bar: (sent + failed + cancelled) / total (REQ-CO-06 Scenarios 1–2)
- [ ] Summary counters: "{total} mensajes — {pendientes} pendientes, {enviando} enviando, {enviados} enviados, {fallidos} fallidos" (REQ-CO-03 Scenario 1)
- [ ] Per-message list: name, email, state badge with appropriate icon/color (REQ-CO-03 Scenario 4)
- [ ] Individual actions: "Cancelar" on pendiente/enviando, "Reintentar" on fallido (REQ-CO-05 Scenarios 1–2)
- [ ] Terminal state: "Comunicación completada" / "Cancelado" message + "Volver" button (REQ-CO-03 Scenarios 2–3)
- [ ] Polling warning: subtle "Actualizando..." when poll request fails (REQ-CO-03 Scenario 6)

### Task T-8.4: Create LoteActions component

- **File**: `frontend/src/features/comisiones/components/LoteActions.tsx`
- [ ] Visible when user has `comunicacion:aprobar` permission (REQ-CO-04 Scenario 4)
- [ ] "Aprobar lote" button: confirmation dialog → POST approve (REQ-CO-04 Scenario 1)
- [ ] "Cancelar lote" button: confirmation dialog → POST cancel (REQ-CO-04 Scenario 2)
- [ ] Loading states: spinner on action buttons while in flight
- [ ] Error handling: toast + keep buttons visible (REQ-CO-04 Scenario 3)
- [ ] Hidden once lote is in terminal state (REQ-CO-04 Scenario 1)

### Task T-8.5: Create ComunicacionesTab component

- **File**: `frontend/src/features/comisiones/components/ComunicacionesTab.tsx`
- [ ] Wraps tracking view for active lote (passed via state or URL)
- [ ] Shows empty state if no active lote: "No hay comunicaciones activas"
- [ ] Integrates `<ComunicacionTracking />` and `<LoteActions />`
- [ ] Handles "Volver" navigation to atrasados tab

---

## Phase 9: Clear Data

### Task T-9.1: Create useClearData hook

- **File**: `frontend/src/features/comisiones/hooks/useClearData.ts`
- [ ] `useClearData(materiaId)` — `useMutation` calling `comisionesApi.clearData(materiaId)`
- [ ] On success: invalidates `['analisis', materiaId]` and `['umbral', materiaId]` queries

### Task T-9.2: Create ClearDataDialog component

- **File**: `frontend/src/features/comisiones/components/ClearDataDialog.tsx`
- [ ] Confirmation dialog: title "¿Vaciar datos de {materia}?", body "Esta acción eliminará todas las calificaciones, umbrales, y análisis. No se puede deshacer." (REQ-GI-06 Scenario 1)
- [ ] "Cancelar" and "Confirmar vaciado" buttons (REQ-GI-06 Scenario 1)
- [ ] Loading: "Confirmar vaciado" shows spinner + disabled, "Cancelar" disabled (REQ-GI-06 Scenario 4)
- [ ] Success: toast + navigate back to commission selector (REQ-GI-06 Scenario 1)
- [ ] Cancel: dismiss dialog, no API call (REQ-GI-06 Scenario 2)
- [ ] Failure: error toast, dialog closes (REQ-GI-06 Scenario 3)

---

## Phase 10: Final Integration

### Task T-10.1: Link all tab components in ComisionDetailPage

- [ ] Wire all tab imports and ensure each receives `materiaId` prop
- [ ] Verify `<Outlet />` routing matches `TabNav` paths

### Task T-10.2: Wire communication flow across AtrasadosTab

- [ ] `AtrasadosTab` passes selected `alumno_ids` to `ComunicacionPreview`
- [ ] On successful send (`useComunicacionEnviar`), navigate to tracking view
- [ ] `ComunicacionesTab` receives `loteId` and shows tracking

### Task T-10.3: Add debounce on monitor filters

- [ ] Create or import `useDebounce` utility (300ms)
- [ ] Apply to text filter inputs in `MonitorFilters` before passing to `useMonitor`

### Task T-10.4: Integrate ClearDataDialog

- [ ] Place `ClearDataDialog` trigger in a settings/actions area of `ComisionDetailPage`
- [ ] On success, navigate back to `/comisiones` (commission selector)

### Task T-10.5: Sidebar check

- [ ] Verify `NAV_ITEMS` in `Sidebar.tsx` includes `{ label: 'Comisiones', path: '/comisiones', icon: LayoutGrid, permission: 'comisiones:read' }`
- [ ] Verify `DashboardHome.tsx` ROUTE_PRIORITY includes `{ path: '/comisiones', permission: 'comisiones:read' }`

### Task T-10.6: Mutation → invalidation matrix verification

Verify all mutations invalidate the correct queries per design §3:

| Mutation | Must invalidate | Check |
|----------|----------------|-------|
| `useImportConfirm(materiaId)` | `['analisis', materiaId]` | [ ] |
| `useImportFinalizacion(materiaId)` | `['analisis', materiaId, 'tps-sin-corregir']` | [ ] |
| `useUmbralMutation(materiaId)` | `['umbral', materiaId]` | [ ] |
| `useClearData(materiaId)` | `['analisis', materiaId]`, `['umbral', materiaId]` | [ ] |
| `useComunicacionEnviar()` | nothing (returns loteId, client navigates) | [ ] |
| `useComunicacionAction(loteId)` | `['comunicaciones', 'lote', loteId]` | [ ] |

### Task T-10.7: Verify all loading/empty/error states across all tabs

Ensure every tab component handles these three states per spec requirements:

- [ ] **ResumenTab**: skeleton cards, empty KPI state, error + retry
- [ ] **ImportarTab**: upload spinner, preview loaded, success/partial error/failure
- [ ] **UmbralTab**: skeleton slider, loaded, error + retry
- [ ] **AtrasadosTab**: skeleton rows, empty success state, error + retry
- [ ] **RankingTab**: skeleton rows, empty with import link, error + retry
- [ ] **NotasFinalesTab**: skeleton rows + spinner on export, empty + disabled export, error + retry
- [ ] **TpsSinCorregirTab**: skeleton rows, empty, error + retry
- [ ] **MonitorTab**: skeleton rows + disabled filters, empty, error + previous data
- [ ] **ComunicacionesTab**: preview loading, tracking polling, empty state
