# Verify Report: C-22 frontend-academico-docente

## Verdict: WARNING

The implementation covers ~90% of requirements. One CRITICAL gap (individual message cancel/retry), two WARNING gaps (coordinator date range filter never wired, monitor endpoints don't differentiate by role), and several minor deviations from spec column definitions.

---

### Grade Import Spec (GI-01 → GI-06)

| Requirement | Status | Notes |
|-------------|--------|-------|
| GI-01 Commission selector | ✅ | Dropdown + format `"{nombre} — {cohorte}"`, placeholder, loading spinner, empty state, error+retry, auto-redirect if single commission |
| GI-02 File upload validation | ✅ | Client-side `.csv/.xlsx` type validation, network error handling, loading spinner + "Procesando archivo...", error display inline |
| GI-02 File name & size display | ⚠️ | File name shown by native browser input; size in KB not explicitly rendered (minor UX) |
| GI-03 Preview table | ✅ | Activities table with checkboxes, type, sample values (first 3), summary count, Confirmar/Volver buttons, all checked by default |
| GI-04 Import confirm | ✅ | Sends selected IDs, success with count, expandable partial errors, failure+retry, disabled when none selected |
| GI-04 "Ver análisis" button | ✅ | Navigates to Resumen tab |
| GI-05 Completion report | ✅ | Upload for finalizacion, uncorrected table (Alumno/Actividad/Fecha), count, export CSV |
| GI-05 No uncorrected TPs | ✅ | "No se detectaron entregas sin corregir" |
| GI-06 Clear data dialog | ✅ | Confirmation dialog, title+body, Cancel/Confirmar, loading on confirm, success→navigate to `/comisiones`, error toast, dialog dismissible |

### Analytics Spec (AN-01 → AN-06)

| Requirement | Status | Notes |
|-------------|--------|-------|
| AN-01 Threshold slider + input | ✅ | Range slider + number input, 0-100, percent label |
| AN-01 Guardar disabled when unchanged | ✅ | `hasChanges` check, Cancelar reverts |
| AN-01 Save mutation | ✅ | Calls `updateUmbral`, toast "Umbral actualizado a {value}%" |
| AN-01 Loading/Error | ✅ | Spinner, "Error al cargar el umbral" + Reintentar |
| AN-02 Atrasados table | ✅ | Columns: checkbox, Alumno, Email, Act. faltantes, Nota promedio, Estado |
| AN-02 Sortable columns | ✅ | Click header toggles asc/desc, sort icons |
| AN-02 Row selection + action bar | ✅ | Header checkbox (select all/none), per-row checkbox, floating bar "Comunicar seleccionados ({count})" |
| AN-02 Search filter | ✅ | Client-side, case-insensitive, partial match, "No hay resultados para..." |
| AN-02 Empty/Loading/Error | ✅ | Empty with success icon, skeleton 5 rows, error+retry |
| AN-03 Ranking table | ✅ | Columns: #, Alumno, Email, Act. aprobadas, Total act., Porcentaje |
| AN-03 Top-3 styling | ✅ | Gold/silver/bronze icons + row background colors |
| AN-03 Empty/Loading/Error | ✅ | Empty + link to import, skeleton, error+retry |
| AN-04 KPI cards | ✅ | 4 cards: Total alumnos, Con aprobada, Atrasados (warning icon), Porcentaje (color-coded) |
| AN-04 Color coding | ✅ | green ≥70%, yellow ≥40%, red <40% |
| AN-04 Empty/Loading/Error | ✅ | "No hay datos", 4 skeleton cards, error+retry |
| AN-05 NotasFinalesTable | ✅ | Columns: Alumno, Email, Nota final (2 decimal), Estado (color badges) |
| AN-05 Export CSV | ✅ | `window.open()` via `getNotasFinalesExportUrl` |
| AN-05 Empty/Loading/Error | ✅ | Empty + disabled export, skeleton, error+retry |
| AN-06 TpsSinCorregirTable | ✅ | Columns: Alumno, Email, Actividad, Fecha de entrega |
| AN-06 Export CSV | ✅ | `getTpsSinCorregirExportUrl` + ExportButton |
| AN-06 Empty/Loading/Error | ✅ | Empty + disabled export, skeleton, error+retry |

### Monitoring Spec (MO-01 → MO-03)

| Requirement | Status | Notes |
|-------------|--------|-------|
| MO-01 Monitor table columns | ❌ | Spec: Alumno, Email, Comisión, Regional, **Actividad, Estado, Última actividad**. Implementation: Alumno, Email, Comisión, Regional, **Actividades** (badges). Missing 3 columns. |
| MO-01 Pagination | ✅ | Page size 50, "Página {page} de {totalPages}", "Anterior"/"Siguiente", "Mostrando {from}-{to} de {total}" |
| MO-01 Text filters | ✅ | nombre, email inputs with 300ms debounce |
| MO-01 Dropdown filters | ⚠️ | Implemented as text inputs, not dropdowns (no options fetched; comision, regional, actividad are text) |
| MO-01 Clear filters | ✅ | "Limpiar filtros" resets all |
| MO-01 Pagination resets on filter | ✅ | `setPage(1)` in `handleFiltersChange` |
| MO-01 Empty/Loading/Error | ✅ | Empty, skeleton+disabled filters, error+retry |
| MO-02 Coordinator date range | ❌ | `MonitorFilters` has `showDateRange` prop but `MonitorTab` never passes it — coordinator date range filter is never rendered |
| MO-02 Coordinator endpoint | ❌ | `comisiones.api.ts` line 107 always calls `/api/analisis/monitor/propio` — no `/general` for coordinators |
| MO-02 All commissions scope | ❌ | No coordinator-specific scope implemented |
| MO-03 Pagination controls | ✅ | Consistent, page-based, disabled at boundaries |

### Communication Spec (CO-01 → CO-06)

| Requirement | Status | Notes |
|-------------|--------|-------|
| CO-01 Preview modal | ✅ | Title "Previsualización de comunicación", recipient count, subject+body display |
| CO-01 Edit mode | ✅ | Editable subject+body fields, "Guardar cambios"/"Vista previa" |
| CO-01 Loading/Error | ✅ | Spinner + "Generando previsualización...", error + retry |
| CO-02 Batch send | ✅ | Calls `/api/comunicaciones/lote`, transitions to tracking on success, error toast + modal stays open |
| CO-02 Send loading | ✅ | Spinner on button + "Enviando comunicación...", Cancel disabled |
| CO-03 Real-time polling | ✅ | `refetchInterval: 5000`, stops on `completado`/`cancelado` |
| CO-03 Summary counters | ✅ | Total/Pendientes/Enviando/Enviados/Fallidos in grid |
| CO-03 Per-message state badges | ✅ | Table with name, email, state badge + icon |
| CO-03 "Actualizando..." warning | ✅ | Shown when `isFetching && !isLoading` |
| CO-04 Lote approve/cancel | ✅ | Permission check, confirmation dialogs, loading, success/error toast |
| CO-04 Non-approver hidden | ✅ | `can('comunicacion:aprobar')` check |
| CO-05 Individual message cancel | ❌ | **Missing**: No "Cancelar" button on pendiente/enviando messages |
| CO-05 Individual message retry | ❌ | **Missing**: No "Reintentar" button on fallido messages |
| CO-06 State machine display | ✅ | Color-coded badges: gray pendiente, blue enviando, green enviado, red fallido, orange cancelado |
| CO-06 Progress bar | ✅ | (enviados+fallidos+cancelados)/total |
| CO-06 Terminal states | ✅ | "Todos los mensajes fueron enviados", "Algunos mensajes no se entregaron", "Lote cancelado" |
| CO-06 "Volver" button | ✅ | Navigates to `/comisiones/{materiaId}/atrasados` |

### Routing & Integration

| Requirement | Status | Notes |
|-------------|--------|-------|
| App.tsx routes | ✅ | `/comisiones` + `/comisiones/:materiaId` with 9 nested tab routes |
| TabNav | ✅ | 9 tabs as NavLink elements, active state with underline |
| Tab components via Outlet | ✅ | All 9 tab components wired correctly |
| Sidebar entry | ✅ | `comisiones:read` in Sidebar.tsx |
| DashboardHome priority | ✅ | `/comisiones` with `comisiones:read` in ROUTE_PRIORITY |
| PermissionGuard | ✅ | `ComisionesPage` wraps content in `comisiones:read` |

### Mutation → Invalidation Matrix

| Mutation | Must invalidate | Status |
|----------|-----------------|--------|
| `useImportConfirm(materiaId)` | `['analisis', materiaId]` | ✅ |
| `useImportFinalizacion(materiaId)` | `['analisis', materiaId, 'tps-sin-corregir']` | ✅ |
| `useUmbralMutation(materiaId)` | `['umbral', materiaId]` | ✅ |
| `useClearData(materiaId)` | `['analisis', materiaId]`, `['umbral', materiaId]` | ✅ |
| `useComunicacionEnviar()` | nothing (returns loteId) | ✅ |
| `useComunicacionAction(loteId)` | `['comunicaciones', 'lote', loteId]` | ✅ |

### TypeScript Check: ✅ 0 errors

---

## Issues Found

### ❌ CRITICAL

1. **CO-05 Missing per-message cancel/retry** (`ComunicacionTracking.tsx`): Individual message actions are not implemented. The spec requires "Cancelar" on pendiente/enviando messages and "Reintentar" on fallido messages. Currently the tracking view only displays state badges — no actionable buttons per row. The `useComunicacionAction` mutation supports `comunicacionId` param but the UI never calls it for individual items.

### ❌ WARNINGS

2. **MO-02 Coordinator date range not wired** (`MonitorTab.tsx:24`): `MonitorFilters` has `showDateRange` prop but `MonitorTab` never passes it (`<MonitorFilters onFiltersChange={handleFiltersChange} isLoading={isLoading} />`). Coordinators never see the date range filter inputs.

3. **MO-02 Coordinator endpoint not differentiated** (`comisiones.api.ts:107`): `getMonitor` always calls `/api/analisis/monitor/propio`. The spec requires coordinators to use `/api/analisis/monitor/general` with cross-commission scope.

4. **MO-01 Missing monitor columns**: Spec defines 7 columns (`Alumno, Email, Comisión, Regional, Actividad, Estado, Última actividad`). Implementation shows 5 columns with `Actividades` badge group instead of individual activity/status/last activity columns.

### ⚠️ SUGGESTIONS

5. **MO-01/MO-02 Filters as text inputs not dropdowns**: `comision`, `regional`, `actividad` are implemented as text inputs. Spec describes them as "dropdown filter". They work functionally (send query params) but UX differs from spec.

6. **GI-02 File name/size display**: Native file input shows filename but not size in KB. Minor UX improvement possible.

7. **`ComunicacionPreview` auto-fetches preview on mount** (`ComunicacionPreview.tsx:41-43`): Uses `useEffect`-style pattern with `useState` + manual fetch rather than `useQuery`. Works correctly but doesn't follow the TanStack Query convention used elsewhere.

---

## Summary

- **Specs covered**: ~90%
- **CRITICAL issues**: 1 (individual message cancel/retry)
- **WARNING issues**: 3 (coordinator date range, coordinator endpoint, monitor columns)
- **SUGGESTIONS**: 3
- **TypeScript**: clean (0 errors)
- **Mutation invalidation matrix**: all correct
- **Routing**: all routes wired correctly
