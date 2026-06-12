# Design: C-22 — Frontend Académico Docente

## 1. Routing Structure

### Route tree (added to `App.tsx`)

```tsx
// Inside <Route element={<Layout />}>
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

### Design decisions

- `ComisionesPage` is the top-level entry. It renders `PermissionGuard` with `comisiones:read` and then shows either a redirect to the first available commission or a `ComisionSelector` if the user has multiple.
- `ComisionDetailPage` renders the tab navigation bar + `<Outlet />`. The `materiaId` param stays in the URL — shareable, back-button safe, and drives all query keys.
- Tabs are rendered as `<NavLink>` elements styled like sidebar sub-items. The active tab matches `location.pathname` against each tab path.
- No sub-layout component needed — `ComisionDetailPage` handles the tabs + Outlet directly.

### App.tsx edit

Add import for `ComisionesPage` and `ComisionDetailPage`, then insert the route block after the `/` route inside `<Route element={<Layout />}>`.

---

## 2. Component Tree

```
<ComisionesPage>                              ← PermissionGuard + redirect/logic
  ├─ <ComisionSelector />                     ← dropdown, shown when materiaId is not selected
  └─ (redirect to /comisiones/:firstId)

<ComisionDetailPage>                          ← tabs + <Outlet />
  ├─ <TabNav />                               ← horizontal tab bar (NavLink per tab)
  └─ <Outlet />                               ← renders current tab component

  Tabs (rendered via Outlet):
  ├─ <ResumenTab />                           ← KPI cards (total, aprobados, pendientes)
  ├─ <ImportarTab />                          ← GradeUploader → ActivitySelector → confirm
  ├─ <UmbralTab />                            ← ThresholdEditor (slider + save)
  ├─ <AtrasadosTab />                         ← AtrasadosTable + selection → ComunicacionPreview
  ├─ <RankingTab />                           ← RankingTable
  ├─ <NotasFinalesTab />                      ← NotasFinalesTable + ExportButton
  ├─ <TpsSinCorregirTab />                    ← TpsSinCorregirTable + ExportButton
  ├─ <MonitorTab />                           ← MonitorFilters + MonitorTable
  └─ <ComunicacionesTab />                    ← ComunicacionTracking + LoteActions
```

### Shared/utility components (reusable across tabs)

- **GradeUploader** — file input (`.csv,.xlsx`), loading overlay, error display. Used in ImportarTab.
- **ActivitySelector** — checkbox table for selecting which activities to include in import.
- **AtrasadosTable** — sortable table with per-row checkbox for communication targeting.
- **RankingTable** — read-only sorted table.
- **NotasFinalesTable** — read-only table with export button.
- **ExportButton** — triggers CSV download via `window.open()` to direct API URL.
- **ThresholdEditor** — number input or slider, percentage display, save button with optimistic update.
- **MonitorFilters** — filter bar (text search, comision, activity dropdown, date range for COORDINADOR).
- **MonitorTable** — data table with pagination (page-based, backend-paginated).
- **ComunicacionPreview** — modal/drawer showing subject + body as recipient sees it, confirm/cancel.
- **ComunicacionTracking** — per-lote state badges (Pendiente/Enviando/Completado/Error).
- **LoteActions** — approve/cancel/retry buttons per lote.
- **ClearDataDialog** — confirmation dialog before clearing commission data.

---

## 3. Data Flow

### TanStack Query ecosystem

```
┌──────────────────────────────────────────────────────┐
│                    ComisionDetailPage                 │
│  (holds materiaId from useParams)                     │
│  ↓ passes materiaId to each tab component             │
├──────────────────────────────────────────────────────┤
│   ResumenTab      → useReporteRapido(materiaId)       │
│   ImportarTab     → useImportPreview(), useImport()   │
│   UmbralTab       → useUmbral(materiaId)             │
│   AtrasadosTab    → useAtrasados(materiaId)           │
│   RankingTab      → useRanking(materiaId)             │
│   NotasFinalesTab → useNotasFinales(materiaId)        │
│   TpsSinCorregir  → useTpsSinCorregir(materiaId)      │
│   MonitorTab      → useMonitor(filters)               │
│   Comunicaciones  → useComunicacionEstado(loteId)     │
└──────────────────────────────────────────────────────┘
```

### Query key convention

```
['comisiones', 'materias', userId]         — user's available commissions
['analisis', materiaId, 'reporte-rapido']  — quick report KPIs
['analisis', materiaId, 'atrasados']       — at-risk students
['analisis', materiaId, 'ranking']         — ranking
['analisis', materiaId, 'notas-finales']   — final grades
['analisis', materiaId, 'tps-sin-corregir']— uncorrected TPs
['analisis', materiaId, 'monitor', filters]— monitoring
['umbral', materiaId]                      — threshold
['comunicaciones', 'lote', loteId]         — lote status (polled)
```

### Mutation → invalidation matrix

| Mutation | Invalidates |
|----------|------------|
| `useImportConfirm(materiaId)` | `['analisis', materiaId]` (all analysis queries under that materia) |
| `useImportFinalizacion(materiaId)` | `['analisis', materiaId, 'tps-sin-corregir']` |
| `useUmbralMutation` | `['umbral', materiaId]` |
| `useClearData` | `['analisis', materiaId]`, `['umbral', materiaId]` |
| `useComunicacionEnviar` | nothing (returns loteId, client navigates to tracking) |
| `useComunicacionAction` | `['comunicaciones', 'lote', loteId]` |

### File upload flow

```
<input type="file" accept=".csv,.xlsx" onChange={handleFileSelect} />
  → setLoading(true)
  → new FormData() + file.append('file', selectedFile)
  → api.post('/api/v1/calificaciones/preview', formData, {
       headers: { 'Content-Type': 'multipart/form-data' }
     })
  → setPreview(response.data)
  → setLoading(false)
  → on error: display structured error (per-row or general)
```

**Why FormData through the shared `api` instance**: The Axios interceptor attaches the Bearer token automatically. Axios detects `FormData` and sets `Content-Type: multipart/form-data` with the correct boundary. No custom header fiddling needed.

### CSV export flow

```
// In ExportButton component:
<button onClick={() => window.open(exportUrl, '_blank')} />

// Or via Axios blob (for POST-based exports):
const { data } = await api.get(url, { params: { materia_id }, responseType: 'blob' });
const blobUrl = URL.createObjectURL(data);
const anchor = document.createElement('a');
anchor.href = blobUrl;
anchor.download = 'notas-finales.csv';
anchor.click();
URL.revokeObjectURL(blobUrl);
```

All export endpoints are GET with `materia_id` param. The simplest approach is `window.open()` to the API URL with query params. The API returns `Content-Disposition: attachment; filename="..."` header.

### Polling for communication tracking

```ts
useQuery({
  queryKey: ['comunicaciones', 'lote', loteId],
  queryFn: () => comisionesApi.getLoteStatus(loteId),
  refetchInterval: (query) => {
    const data = query.state.data;
    if (!data) return 5000;
    // Terminal states: stop polling
    if (data.estado === 'Completado' || data.estado === 'Cancelado') return false;
    return 5000;
  },
});
```

---

## 4. Key Types (`features/comisiones/types/comisiones.types.ts`)

```ts
// ── Commission ──
export interface MateriaCohorte {
  id: string;
  materia_id: string;
  materia_nombre: string;
  cohorte_nombre: string;
}

// ── Grade Import ──
export interface ActivityDTO {
  id: string;
  nombre: string;
  tipo: string;
  fecha: string;
  filas_detectadas: number;
}

export interface AlumnoPreviewDTO {
  legajo: string;
  nombre: string;
  email: string;
  notas_detectadas: number;
}

export interface ImportPreviewResponse {
  actividades: ActivityDTO[];
  alumnos: AlumnoPreviewDTO[];
}

export interface ImportConfirmRequest {
  materia_id: string;
  activities_selected: string[];  // activity IDs
}

export interface ImportError {
  row: number;
  legajo?: string;
  mensaje: string;
}

export interface ImportConfirmResponse {
  imported_count: number;
  errors: ImportError[];
}

// ── Threshold ──
export interface Umbral {
  umbral_pct: number;  // 0–100
}

// ── Analytics ──
export interface Atrasado {
  alumno_id: string;
  nombre: string;
  email: string;
  actividades_faltantes: number;
  nota_promedio: number | null;
  estado: string;  // 'regular' | 'promociona' | 'libre'
}

export interface RankingEntry {
  alumno_id: string;
  nombre: string;
  email: string;
  actividades_aprobadas: number;
  total_actividades: number;
}

export interface ReporteRapido {
  total_alumnos: number;
  aprobados: number;
  pendientes: number;
  promocionan: number;
  libres: number;
}

export interface NotaFinal {
  alumno_id: string;
  nombre: string;
  email: string;
  nota_final: number | null;
  estado: string;  // 'aprobado' | 'desaprobado' | 'pendiente' | 'libre' | 'promociona'
}

export interface TpsSinCorregirEntry {
  alumno_id: string;
  nombre: string;
  actividad: string;
  fecha_entrega: string;
}

// ── Monitoring ──
export interface MonitorFilters {
  nombre?: string;
  email?: string;
  actividad?: string;
  comision?: string;
  regional?: string;
  min_actividades_completadas?: number;
  fecha_desde?: string;   // COORDINADOR only
  fecha_hasta?: string;   // COORDINADOR only
}

export interface MonitorEntry {
  alumno_id: string;
  nombre: string;
  email: string;
  materia: string;
  comision: string;
  regional: string;
  estado_actividades: {
    actividad_id: string;
    nombre: string;
    aprobada: boolean;
    nota: number | null;
  }[];
}

// ── Communications ──
export interface ComunicacionPreviewRequest {
  materia_id: string;
  alumno_ids: string[];
}

export interface ComunicacionPreview {
  asunto: string;
  cuerpo: string;
}

export interface ComunicacionEnviarRequest {
  materia_id: string;
  alumno_ids: string[];
  asunto: string;
  cuerpo: string;
}

export interface ComunicacionEnviarResponse {
  lote_id: string;
}

export interface ComunicacionItem {
  id: string;
  alumno_nombre: string;
  alumno_email: string;
  estado: string;  // 'pendiente' | 'enviado' | 'fallido' | 'cancelado'
  error?: string;
}

export interface ComunicacionLote {
  lote_id: string;
  estado: string;           // 'pendiente' | 'enviando' | 'completado' | 'cancelado'
  requiere_aprobacion: boolean;
  items: ComunicacionItem[];
}

export interface LoteActionResponse {
  success: boolean;
}
```

---

## 5. Hook Design

All hooks under `features/comisiones/hooks/`. Each hook imports from `features/comisiones/services/comisiones.api.ts` and uses `@tanstack/react-query`.

### `useComisiones.ts`

```ts
function useComisiones() {
  return useQuery<MateriaCohorte[]>({
    queryKey: ['comisiones', 'materias'],
    queryFn: comisionesApi.getMisComisiones,
    staleTime: 5 * 60 * 1000,
  });
}
```

**Source of commission list**: extracted from `useAuth().user` via `/api/auth/me`, or a dedicated endpoint. If `MeResponse` already includes `comisiones` or a `materias` array, use that. Otherwise call `GET /api/v1/calificaciones` to list available materia+cohorte pairs for the current user. The exact endpoint depends on C-10's implementation — the hook abstracts this.

### `useCalificaciones.ts`

```ts
function useImportPreview() {
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return comisionesApi.importPreview(formData);
    },
  });
}

function useImportConfirm(materiaId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (activities_selected: string[]) =>
      comisionesApi.importConfirm({ materia_id: materiaId, activities_selected }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analisis', materiaId] });
    },
  });
}

function useImportFinalizacion(materiaId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return comisionesApi.importFinalizacion(formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analisis', materiaId, 'tps-sin-corregir'] });
    },
  });
}
```

### `useUmbral.ts`

```ts
function useUmbral(materiaId: string) {
  return useQuery<Umbral>({
    queryKey: ['umbral', materiaId],
    queryFn: () => comisionesApi.getUmbral(materiaId),
    enabled: !!materiaId,
  });
}

function useUmbralMutation(materiaId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (umbral_pct: number) =>
      comisionesApi.updateUmbral(materiaId, { umbral_pct }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['umbral', materiaId] });
    },
  });
}
```

### `useAtrasados.ts`

```ts
function useAtrasados(materiaId: string) {
  return useQuery<Atrasado[]>({
    queryKey: ['analisis', materiaId, 'atrasados'],
    queryFn: () => comisionesApi.getAtrasados(materiaId),
    enabled: !!materiaId,
  });
}
```

### `useRanking.ts`

```ts
function useRanking(materiaId: string) {
  return useQuery<RankingEntry[]>({
    queryKey: ['analisis', materiaId, 'ranking'],
    queryFn: () => comisionesApi.getRanking(materiaId),
    enabled: !!materiaId,
  });
}
```

### `useReporteRapido.ts`

```ts
function useReporteRapido(materiaId: string) {
  return useQuery<ReporteRapido>({
    queryKey: ['analisis', materiaId, 'reporte-rapido'],
    queryFn: () => comisionesApi.getReporteRapido(materiaId),
    enabled: !!materiaId,
  });
}
```

### `useNotasFinales.ts`

```ts
function useNotasFinales(materiaId: string) {
  return useQuery<NotaFinal[]>({
    queryKey: ['analisis', materiaId, 'notas-finales'],
    queryFn: () => comisionesApi.getNotasFinales(materiaId),
    enabled: !!materiaId,
  });
}
```

**Export**: Not a hook but a utility function or direct `window.open()` call — no query caching needed for file downloads.

### `useTpsSinCorregir.ts`

```ts
function useTpsSinCorregir(materiaId: string) {
  return useQuery<TpsSinCorregirEntry[]>({
    queryKey: ['analisis', materiaId, 'tps-sin-corregir'],
    queryFn: () => comisionesApi.getTpsSinCorregir(materiaId),
    enabled: !!materiaId,
  });
}
```

### `useMonitor.ts`

```ts
function useMonitor(materiaId: string, filters: MonitorFilters) {
  return useQuery<MonitorEntry[]>({
    queryKey: ['analisis', materiaId, 'monitor', filters],
    queryFn: () => comisionesApi.getMonitor(materiaId, filters),
    enabled: !!materiaId,
  });
}
```

Filters are debounced client-side before being passed to the hook (300ms debounce in the component using a `useDebounce` utility).

### `useComunicaciones.ts`

```ts
function useComunicacionPreview() {
  return useMutation({
    mutationFn: (data: ComunicacionPreviewRequest) =>
      comisionesApi.previewComunicacion(data),
  });
}

function useComunicacionEnviar() {
  return useMutation({
    mutationFn: (data: ComunicacionEnviarRequest) =>
      comisionesApi.enviarComunicacion(data),
  });
}

function useComunicacionEstado(loteId: string | null) {
  return useQuery<ComunicacionLote>({
    queryKey: ['comunicaciones', 'lote', loteId],
    queryFn: () => comisionesApi.getLoteStatus(loteId!),
    enabled: !!loteId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 5000;
      if (data.estado === 'completado' || data.estado === 'cancelado') return false;
      return 5000;
    },
  });
}

function useComunicacionAction(loteId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ action }: { action: 'approve' | 'cancel' | 'retry';
      comunicacionId?: string }) =>
      comisionesApi.loteAction(loteId, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comunicaciones', 'lote', loteId] });
    },
  });
}
```

### `useClearData.ts`

```ts
function useClearData(materiaId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => comisionesApi.clearData(materiaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analisis', materiaId] });
      queryClient.invalidateQueries({ queryKey: ['umbral', materiaId] });
    },
  });
}
```

---

## 6. File Upload Pattern

### Component: `GradeUploader`

```tsx
interface GradeUploaderProps {
  onPreview: (response: ImportPreviewResponse) => void;
}

function GradeUploader({ onPreview }: GradeUploaderProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const previewMutation = useImportPreview();

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const response = await previewMutation.mutateAsync(file);
      onPreview(response);
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (axios.isAxiosError(err) && err.response?.data?.errors) {
        // Structured per-row errors
        setError(err.response.data.errors.map((e: ImportError) =>
          `Fila ${e.row}: ${e.mensaje}`).join('\n'));
      } else {
        setError('Error al procesar el archivo. Verificá el formato.');
      }
    } finally {
      setIsUploading(false);
      // Reset input so the same file can be re-selected
      e.target.value = '';
    }
  };

  return (
    <div>
      <input
        type="file"
        accept=".csv,.xlsx"
        onChange={handleFile}
        disabled={isUploading}
        className={cn(
          'block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0',
          'file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100',
          isUploading && 'opacity-50 cursor-not-allowed',
        )}
      />
      {isUploading && <Spinner size="sm" className="mt-2" />}
      {error && (
        <div className="mt-2 rounded-md bg-danger-50 p-3 text-sm text-danger-600 whitespace-pre-line">
          {error}
        </div>
      )}
    </div>
  );
}
```

### States per upload lifecycle

| State | Visual |
|-------|--------|
| idle | File input shown, no feedback |
| uploading | Spinner + disabled input |
| preview | ActivitySelector table replaces input |
| confirming | Confirmation button visible |
| success | Success toast, table updates |
| error | Inline alert with error detail |

---

## 7. Sidebar Update

The sidebar (`Sidebar.tsx`) already includes the `Comisiones` entry:

```ts
{ label: 'Comisiones', path: '/comisiones', icon: LayoutGrid, permission: 'comisiones:read' }
```

This is already present in `NAV_ITEMS`. **No changes needed** to `Sidebar.tsx`.

The `DashboardHome.tsx` already has `{ path: '/comisiones', permission: 'comisiones:read' }` in `ROUTE_PRIORITY` — it auto-redirects to `/comisiones` if the user has the permission.

---

## 8. File-by-file Breakdown

### New files in `frontend/src/features/comisiones/`

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 1 | `types/comisiones.types.ts` | All domain types & interfaces | 120 |
| 2 | `services/comisiones.api.ts` | All API call functions | 100 |
| 3 | `hooks/useComisiones.ts` | Fetch user's commission list | 20 |
| 4 | `hooks/useCalificaciones.ts` | Import preview, confirm, finalizacion mutations | 50 |
| 5 | `hooks/useUmbral.ts` | GET + PUT threshold | 35 |
| 6 | `hooks/useAtrasados.ts` | GET at-risk students | 20 |
| 7 | `hooks/useRanking.ts` | GET ranking | 15 |
| 8 | `hooks/useReporteRapido.ts` | GET quick report KPIs | 15 |
| 9 | `hooks/useNotasFinales.ts` | GET final grades | 15 |
| 10 | `hooks/useTpsSinCorregir.ts` | GET uncorrected TPs | 15 |
| 11 | `hooks/useMonitor.ts` | GET monitoring with filters | 25 |
| 12 | `hooks/useComunicaciones.ts` | Preview, send, status, approve/cancel/retry | 65 |
| 13 | `hooks/useClearData.ts` | Clear commission data mutation | 20 |
| 14 | `pages/ComisionesPage.tsx` | Entry: PermissionGuard + commission redirect | 35 |
| 15 | `pages/ComisionDetailPage.tsx` | Tabs layout with Outlet | 60 |
| 16 | `components/TabNav.tsx` | Reusable horizontal tab navigation | 40 |
| 17 | `components/ComisionSelector.tsx` | Materia+cohorte dropdown | 50 |
| 18 | `components/GradeUploader.tsx` | File input + loading state | 55 |
| 19 | `components/ActivitySelector.tsx` | Checkbox list from preview | 60 |
| 20 | `components/ThresholdEditor.tsx` | Slider/number input + save | 55 |
| 21 | `components/AtrasadosTable.tsx` | Sortable table + row selection | 85 |
| 22 | `components/RankingTable.tsx` | Sorted ranking table | 50 |
| 23 | `components/ReportesSummary.tsx` | KPI card grid | 45 |
| 24 | `components/NotasFinalesTable.tsx` | Final grades table | 55 |
| 25 | `components/ExportButton.tsx` | CSV download button | 30 |
| 26 | `components/TpsSinCorregirTable.tsx` | Uncorrected TPs table | 50 |
| 27 | `components/MonitorTable.tsx` | Data table with pagination | 80 |
| 28 | `components/MonitorFilters.tsx` | Filter bar (text, select, date) | 70 |
| 29 | `components/ComunicacionPreview.tsx` | Preview modal/drawer | 65 |
| 30 | `components/ComunicacionTracking.tsx` | Lote state badges + item list | 60 |
| 31 | `components/LoteActions.tsx` | Approve/cancel/retry buttons | 45 |
| 32 | `components/ClearDataDialog.tsx` | Confirmation dialog | 45 |
| 33 | `components/ResumenTab.tsx` | Wraps ReportesSummary | 20 |
| 34 | `components/ImportarTab.tsx` | Upload → preview → confirm flow | 80 |
| 35 | `components/UmbralTab.tsx` | Wraps ThresholdEditor | 15 |
| 36 | `components/AtrasadosTab.tsx` | Wraps AtrasadosTable + ComunicacionPreview | 65 |
| 37 | `components/RankingTab.tsx` | Wraps RankingTable | 15 |
| 38 | `components/NotasFinalesTab.tsx` | Wraps NotasFinalesTable + ExportButton | 20 |
| 39 | `components/TpsSinCorregirTab.tsx` | Wraps TpsSinCorregirTable + ExportButton | 20 |
| 40 | `components/MonitorTab.tsx` | Wraps MonitorFilters + MonitorTable | 25 |
| 41 | `components/ComunicacionesTab.tsx` | Wraps ComunicacionTracking + LoteActions | 40 |

**Total: ~40 files, ~1720 LOC** (excluding blank lines and imports).

### Modified files

| # | File | Change |
|---|------|--------|
| 1 | `frontend/src/App.tsx` | Add route imports + route block for `/comisiones` |
| 2 | `frontend/src/shared/components/Sidebar.tsx` | Already has the entry — no change needed |

---

## 9. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Large file uploads (>10MB CSV/XLSX)** | Long upload time, no feedback | Backend parses the file, frontend only renders JSON response. Show progress via Axios `onUploadProgress` if needed. Set `maxBodySize` on nginx/reverse proxy. |
| **Polling with many concurrent lotes** | Excessive network requests | Only one active lote per materiaId at a time. Polling stops when lote reaches terminal state (`completado`/`cancelado`). Use `refetchInterval` conditional return. |
| **Permission filtering of commissions** | Teacher sees another's commission in dropdown, gets 403 | Backend enforces RBAC per endpoint (fail-closed). Frontend pre-filters from session data (user's assigned materias). If 403 received, show inline error and force re-fetch of commission list. |
| **Stale data after import** | User sees old analysis data | `onSuccess` of import mutation invalidates all `['analisis', materiaId]` queries. TanStack Query auto-refetches stale queries when tabs are focused. |
| **CSV export browser compatibility** | Download fails silently | Use Axios blob response + `URL.createObjectURL` + temporary `<a>` click for reliability. Fallback to `window.open()` for simple GET exports. |
| **Race condition on concurrent imports** | First import overwritten by second | Backend locks per materia_id. Frontend disables import button while mutation is in-flight (`isPending` from `useMutation`). |
| **User navigates away mid-upload** | Mutation state lost | TanStack Query keeps the promise. On re-mount, the mutation is not re-executed. Show toast on success regardless of navigation. |
| **Large monitoring dataset (1000+ students)** | UI freeze rendering rows | Backend paginates (page-based). Frontend renders one page at a time. Use virtualized table (`@tanstack/react-virtual`) only if pagination is insufficient. |
| **Error messages from backend are generic** | User can't fix file format issues | Backend returns per-row structured errors (`ImportError[]`). Frontend renders them grouped: "5 errores encontrados" with expandable details. |

---

## Implementation Order (tasks.md alignment)

The implementation follows the dependency graph of the proposal's integration points:

1. **Types + API service** — no dependencies, foundation for everything
2. **Pages + routing** — `ComisionesPage`, `ComisionDetailPage`, `TabNav`, update `App.tsx`
3. **Commission selector** — `useComisiones`, `ComisionSelector`
4. **Threshold** — `useUmbral`, `ThresholdEditor`, `UmbralTab` (simplest CRUD)
5. **Grade import flow** — `useCalificaciones`, `GradeUploader`, `ActivitySelector`, `ImportarTab`
6. **Analysis views (parallelizable)** — atrasados, ranking, reportes, notas-finales, tps-sin-corregir
7. **Monitoring** — `useMonitor`, `MonitorFilters`, `MonitorTable`, `MonitorTab`
8. **Communications** — `useComunicaciones`, `ComunicacionPreview`, `ComunicacionTracking`, `LoteActions`, `ComunicacionesTab`
9. **Clear data** — `useClearData`, `ClearDataDialog`
10. **Final integration** — link all tabs, test flows, add debounce on monitor filters

Tabs 5–6 can be built in parallel (separate hook files, separate tab components). Tab 8 depends on tab 6 (at-risk selection drives communication targeting).
