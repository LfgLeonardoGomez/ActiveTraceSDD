# Design: C-23 — Frontend Coordinación

## 1. Technical Approach

This change builds the complete **Coordinación module** as a new feature island under `features/coordinacion/`, following the exact same architecture as C-22 (frontend-academico-docente):

- **Feature-based directory**: each of the 7 domains (equipos, estructura, encuentros, coloquios, tareas, avisos, monitor) lives as a self-contained sub-module under `features/coordinacion/{components,hooks,services,types,pages}/`
- **TanStack Query v5** for all server state, with scoped query keys prefixed by `['coordinacion', domain, ...]`
- **Axios** via the shared `@/shared/services/api` instance (token refresh interceptor already present)
- **Permission gating** via `usePermissions().can()` at both route level (`PermissionGuard`) and action level (conditional button rendering)
- **File uploads** via FormData (same pattern as C-22 `GradeUploader`)
- **CSV exports** via Axios blob download (same pattern as C-22 `ExportButton`)
- **No WebSocket** — polling via `refetchInterval` for task workflow state transitions
- **Multi-step wizard** for coloquios convocatoria creation and avisos scope/configuration
- **Tailwind CSS v4** with shared UI primitives from `@/shared/components/ui/` (Button with CVA, Card compound, Input forwardRef, Spinner)

The `/coordinacion` route tree mounts under `<Route element={<Layout />}>` alongside the existing `/comisiones` route block.

---

## 2. Architecture Decisions

### AD-01: `CoordinacionLayout` as the section wrapper

A `CoordinacionLayout` component handles the section-level navigation (sub-nav for the 7 domains) and renders `<Outlet />`. Unlike C-22's `ComisionDetailPage` (which uses tabs for sub-sections of a single entity), C-23's layout shows a vertical or horizontal sub-navigation for the 7 independent domains.

Each domain page acts as the entry point for that domain's sub-routes (e.g., `EquiposPages` renders `EquipoTable` at `/coordinacion/equipos` and nested routes at `/coordinacion/equipos/usuarios`, `/coordinacion/equipos/asignaciones`, etc.).

No separate provider wrappers are needed — each domain's hooks are independent and scoped by query key.

### AD-02: Scoped TanStack Query keys per domain

```
['coordinacion', 'equipos', 'mis-equipos', filters]
['coordinacion', 'equipos', 'usuarios']
['coordinacion', 'equipos', 'asignaciones', filters]
['coordinacion', 'estructura', 'carreras']
['coordinacion', 'estructura', 'cohortes']
['coordinacion', 'estructura', 'programas']
['coordinacion', 'estructura', 'evaluaciones', filters]
['coordinacion', 'encuentros', 'list', filters]
['coordinacion', 'encuentros', 'guardias', filters]
['coordinacion', 'coloquios', 'metricas']
['coordinacion', 'coloquios', 'list', filters]
['coordinacion', 'coloquios', 'detail', convocatoriaId]
['coordinacion', 'tareas', 'mis-tareas', filters]
['coordinacion', 'tareas', 'admin', filters]
['coordinacion', 'avisos', 'list', filters]
['coordinacion', 'monitor', 'general', filters]
['coordinacion', 'monitor', 'auditoria', filters]
```

Each domain's hooks are in separate files under `hooks/`. Mutations invalidate queries by the broadest matching prefix (e.g., creating a cohorte invalidates `['coordinacion', 'estructura', 'cohortes']`).

### AD-03: Permission-based sidebar nav with section grouping

The current sidebar is flat. Adding 7 coordinación entries on top of the existing 6 makes it overly long. The sidebar gets a visual section group "Coordinación" with the 7 entries, each gated by its own permission:

| Sidebar entry | Route | Permission |
|---------------|-------|------------|
| Equipos Docentes | `/coordinacion/equipos` | `equipos:ver` |
| Estructura | `/coordinacion/estructura` | `estructura:gestionar` |
| Encuentros | `/coordinacion/encuentros` | `encuentros:ver` |
| Coloquios | `/coordinacion/coloquios` | `coloquios:ver` |
| Tareas | `/coordinacion/tareas` | `tareas:ver` |
| Avisos | `/coordinacion/avisos` | `avisos:ver` |
| Monitor | `/coordinacion/monitor` | `monitor:ver` |

The existing `NAV_ITEMS["Equipos"]` entry (currently pointing to `/equipos`) is replaced — its route changes to `/coordinacion/equipos` and its permission updates to `equipos:ver`. The icon stays `UsersRound`.

Sub-navigation within each domain (e.g., usuarios, asignaciones bajo equipos) is handled by secondary nav in the domain's page component, not in the sidebar.

### AD-04: Multi-step wizard for complex forms

Two forms require wizard patterns:

**Coloquios ConvocatoriaForm** — 3 steps:
1. Datos generales (materia, cohorte, instancia, título)
2. Días y cupos (dynamic list of date + max slots, min 1)
3. Confirmar (read-only summary)

State is lifted to the parent wizard component via a single `FormData` object. Each step validates via Zod before advancing. Step state persists during backward navigation.

**AvisoForm** — conditional sections (not a traditional wizard but a form with progressive disclosure):
1. Alcance toggles (global/materia/cohorte) conditionally show materia/cohorte selectors
2. Roles destinatarios section
3. Vigencia (date range, optional fields)
4. requiere_ack (conditional)

### AD-05: File upload pattern (FormData through Axios)

Identical to C-22:

```ts
const formData = new FormData();
formData.append('file', selectedFile);
// For programas: append metadata too
formData.append('materia_id', materiaId);
formData.append('titulo', title);

const { data } = await api.post('/api/v1/estructura/programas', formData);
```

Axios interceptors attach the Bearer token automatically. Axios detects FormData and sets `Content-Type: multipart/form-data` with correct boundary.

**Affected uploads**:
- Programas de materias (PDF/DOC/DOCX)
- Importar alumnos a coloquio (CSV/XLSX)

### AD-06: Recurrent instance generation UX

When the user submits `EncuentroRecurrenteForm`:

1. Submit `POST /api/v1/encuentros/recurrente`
2. Show inline spinner "Generando instancias..." immediately
3. If response takes >2s, activate polling via `refetchInterval` (every 3s) to `GET /api/v1/encuentros/recurrente/{id}/status`
4. On completion, show success toast with instance count
5. Navigate to the transversal encuentros view

The frontend treats synchronous responses as the fast path (most common for ≤16 weeks) and falls back to polling only when generation is slow.

### AD-07: Task workflow polling (no WebSockets)

Task state transitions use conditional polling:

```ts
useQuery({
  queryKey: ['coordinacion', 'tareas', 'mis-tareas', filters],
  queryFn: () => tareasApi.getMisTareas(filters),
  refetchInterval: (query) => {
    const tasks = query.state.data;
    if (!tasks) return 30000;
    const hasNonTerminal = tasks.some(t =>
      !['completada', 'aprobada', 'rechazada'].includes(t.estado)
    );
    return hasNonTerminal ? 30000 : false;
  },
});
```

When all tasks reach terminal states, polling stops. The admin global view (`TareasAdmin`) also polls but at a lower frequency (60s) since admin actions are less time-sensitive.

---

## 3. Data Flow

### Hook design per domain

Each hook file exports one or more hooks. Standard pattern:

```ts
// Query
function useEquipos() {
  return useQuery<Equipo[]>({
    queryKey: ['coordinacion', 'equipos', 'mis-equipos'],
    queryFn: equiposApi.getMisEquipos,
    staleTime: 5 * 60 * 1000,
  });
}

// Mutation with invalidation
function useCrearAsignacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AsignacionRequest) => equiposApi.crearAsignacion(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'equipos', 'asignaciones'] });
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'equipos', 'mis-equipos'] });
    },
  });
}
```

### Mutation → invalidation matrix

| Domain | Mutation | Invalidates |
|--------|----------|-------------|
| Equipos | crearEditarUsuario | `['coordinacion', 'equipos', 'usuarios']` |
| Equipos | crearAsignacion | `['coordinacion', 'equipos', 'asignaciones']`, `['coordinacion', 'equipos', 'mis-equipos']` |
| Equipos | asignacionMasiva | `['coordinacion', 'equipos', 'asignaciones']` |
| Equipos | clonarEquipo | `['coordinacion', 'equipos', 'asignaciones']` |
| Equipos | actualizarVigencia | `['coordinacion', 'equipos', 'asignaciones']`, `['coordinacion', 'equipos', 'mis-equipos']` |
| Estructura | crearCarrera | `['coordinacion', 'estructura', 'carreras']` |
| Estructura | crearCohorte | `['coordinacion', 'estructura', 'cohortes']` |
| Estructura | subirPrograma | `['coordinacion', 'estructura', 'programas']` |
| Estructura | eliminarPrograma | `['coordinacion', 'estructura', 'programas']` |
| Estructura | crearEvaluacion | `['coordinacion', 'estructura', 'evaluaciones']` |
| Encuentros | crearRecurrente | `['coordinacion', 'encuentros', 'list']` |
| Encuentros | crearUnico | `['coordinacion', 'encuentros', 'list']` |
| Encuentros | editarEncuentro | `['coordinacion', 'encuentros', 'list']` |
| Encuentros | registrarGuardia | `['coordinacion', 'encuentros', 'guardias']` |
| Coloquios | crearConvocatoria | `['coordinacion', 'coloquios', 'list']` |
| Coloquios | importarAlumnos | `['coordinacion', 'coloquios', 'metricas']`, `['coordinacion', 'coloquios', 'detail']` |
| Coloquios | cerrarConvocatoria | `['coordinacion', 'coloquios', 'list']`, `['coordinacion', 'coloquios', 'admin']` |
| Tareas | asignarTarea | `['coordinacion', 'tareas', 'mis-tareas']`, `['coordinacion', 'tareas', 'admin']` |
| Tareas | actualizarEstadoTarea | `['coordinacion', 'tareas']` (all tareas queries) |
| Avisos | crearAviso | `['coordinacion', 'avisos', 'list']` |
| Avisos | editarAviso | `['coordinacion', 'avisos', 'list']` |
| Avisos | eliminarAviso | `['coordinacion', 'avisos', 'list']` |
| Avisos | publicarAviso | `['coordinacion', 'avisos', 'list']` |

---

## 4. Route Structure

Added to `App.tsx` under `<Route element={<Layout />}>`:

```tsx
<Route path="/coordinacion" element={<CoordinacionLayout />}>
  <Route index element={<CoordinacionHome />} />
  <Route path="equipos" element={<EquiposPages />}>
    <Route index element={<EquiposHome />} />
    <Route path="usuarios" element={<AdminUsuarios />} />           {/* ADMIN only */}
    <Route path="asignaciones" element={<AsignacionesList />} />
    <Route path="asignaciones/masiva" element={<AsignacionMasiva />} />
    <Route path="clonar" element={<ClonarEquipo />} />
    <Route path="vigencia" element={<VigenciaEquipo />} />
    <Route path="exportar" element={<ExportarEquipo />} />
  </Route>
  <Route path="estructura" element={<EstructuraPages />}>
    <Route index element={<EstructuraHome />} />
    <Route path="carreras" element={<CarrerasList />} />
    <Route path="cohortes" element={<CohortesList />} />
    <Route path="programas" element={<ProgramasList />} />
    <Route path="evaluaciones" element={<EvaluacionesList />} />
  </Route>
  <Route path="encuentros" element={<EncuentrosPages />}>
    <Route index element={<EncuentrosList />} />
    <Route path="nuevo" element={<CrearEncuentro />} />
    <Route path="recurrente" element={<CrearRecurrente />} />
    <Route path=":encuentroId/editar" element={<EditarEncuentro />} />
    <Route path="guardias" element={<GuardiasList />} />
  </Route>
  <Route path="coloquios" element={<ColoquiosPages />}>
    <Route index element={<ColoquiosDashboard />} />
    <Route path="nuevo" element={<CrearConvocatoria />} />
    <Route path=":convocatoriaId" element={<ConvocatoriaDetail />} />
    <Route path="admin" element={<ColoquiosAdmin />} />             {/* ADMIN only */}
  </Route>
  <Route path="tareas" element={<TareasPages />}>
    <Route index element={<MisTareas />} />
    <Route path="asignar" element={<AsignarTarea />} />
    <Route path="admin" element={<TareasAdmin />} />
  </Route>
  <Route path="avisos" element={<AvisosPages />}>
    <Route index element={<AvisosList />} />
    <Route path="nuevo" element={<CrearAviso />} />
    <Route path=":avisoId/editar" element={<EditarAviso />} />
  </Route>
  <Route path="monitor" element={<MonitorPages />}>
    <Route index element={<MonitorGeneral />} />
    <Route path="auditoria" element={<AuditoriaDocente />} />
  </Route>
</Route>
```

---

## 5. File Changes

### New files in `frontend/src/features/coordinacion/`

#### Types (7 files)

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 1 | `types/equipos.types.ts` | Equipo, Asignacion, UsuarioDocente, AsignacionRequest | 60 |
| 2 | `types/estructura.types.ts` | Carrera, Cohorte, Programa, Evaluacion | 50 |
| 3 | `types/encuentros.types.ts` | Encuentro, Guardia, SerieRecurrenteRequest | 45 |
| 4 | `types/coloquios.types.ts` | Convocatoria, MetricasColoquios, ImportResult, Reserva | 55 |
| 5 | `types/tareas.types.ts` | Tarea, TareaComment, TareaFilters | 40 |
| 6 | `types/avisos.types.ts` | Aviso, AvisoFormData, AckEntry | 40 |
| 7 | `types/monitor.types.ts` | MonitorEntry, AuditoriaEntry, MonitorFilters | 35 |

#### Services (7 files)

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 8 | `services/equipos.api.ts` | All equipo & asignación API calls (7 endpoints) | 70 |
| 9 | `services/estructura.api.ts` | Carreras, cohortes, programas, evaluaciones API calls | 60 |
| 10 | `services/encuentros.api.ts` | Encuentros CRUD, recurrente, guardias, contenido-aula | 65 |
| 11 | `services/coloquios.api.ts` | Metricas, convocatorias CRUD, import, admin | 50 |
| 12 | `services/tareas.api.ts` | Mis tareas, admin, crear, estado transitions | 45 |
| 13 | `services/avisos.api.ts` | Avisos CRUD, publish, ack | 40 |
| 14 | `services/monitor.api.ts` | Monitor general, auditoria | 35 |

#### Hooks (7 files)

| # | File | Exports | Est. LOC |
|---|------|---------|----------|
| 15 | `hooks/useEquipos.ts` | `useMisEquipos`, `useUsuarios`, `useAsignaciones`, `useCrearAsignacion`, `useAsignacionMasiva`, `useClonarEquipo`, `useActualizarVigencia` | 120 |
| 16 | `hooks/useEstructura.ts` | `useCarreras`, `useCrearCarrera`, `useCohortes`, `useCrearCohorte`, `useProgramas`, `useSubirPrograma`, `useEvaluaciones`, `useCrearEvaluacion` | 110 |
| 17 | `hooks/useEncuentros.ts` | `useEncuentros`, `useCrearRecurrente`, `useCrearEncuentro`, `useEditarEncuentro`, `useContenidoAula`, `useGuardias`, `useRegistrarGuardia` | 100 |
| 18 | `hooks/useColoquios.ts` | `useMetricasColoquios`, `useConvocatorias`, `useCrearConvocatoria`, `useImportarAlumnos`, `useConvocatoriaAdmin` | 90 |
| 19 | `hooks/useTareas.ts` | `useMisTareas`, `useAsignarTarea`, `useTareasAdmin`, `useActualizarEstadoTarea` | 75 |
| 20 | `hooks/useAvisos.ts` | `useAvisos`, `useCrearAviso`, `useEditarAviso`, `useEliminarAviso`, `useConfirmarAck` | 65 |
| 21 | `hooks/useMonitorCoordinacion.ts` | `useMonitorGeneral`, `useAuditoria` | 50 |

#### Pages (8 files)

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 22 | `pages/CoordinacionHome.tsx` | Landing dashboard with KPIs across domains | 50 |
| 23 | `pages/EquiposPages.tsx` | Multi-export page with sub-route layout (mis equipos, usuarios, asignaciones, clonar, vigencia, exportar) | 80 |
| 24 | `pages/EstructuraPages.tsx` | Sub-route layout (home, carreras, cohortes, programas, evaluaciones) | 80 |
| 25 | `pages/EncuentrosPages.tsx` | Sub-route layout (list, nuevo, recurrente, editar, guardias) | 70 |
| 26 | `pages/ColoquiosPages.tsx` | Sub-route layout (dashboard metricas, nuevo, detail, admin) | 80 |
| 27 | `pages/TareasPages.tsx` | Sub-route layout (mis-tareas, asignar, admin) | 60 |
| 28 | `pages/AvisosPages.tsx` | Sub-route layout (list, nuevo, editar) | 60 |
| 29 | `pages/MonitorPages.tsx` | Sub-route layout (general, auditoria) | 50 |

#### Layout (1 file)

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 30 | `components/CoordinacionLayout.tsx` | Section navigation + `<Outlet />`, 7 domain sub-nav | 60 |

#### Equipos Components (9 files)

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 31 | `components/equipos/EquipoCard.tsx` | Summary card for mis-equipos view | 40 |
| 32 | `components/equipos/EquipoTable.tsx` | Assignments table with pagination | 60 |
| 33 | `components/equipos/AsignacionForm.tsx` | Individual assignment form | 50 |
| 34 | `components/equipos/AsignacionMasivaForm.tsx` | Multi-select docentes + bulk assign | 60 |
| 35 | `components/equipos/ClonarEquipoForm.tsx` | Origen → destino selectors | 50 |
| 36 | `components/equipos/VigenciaEditor.tsx` | Date range editor + confirm dialog | 45 |
| 37 | `components/equipos/ExportButton.tsx` | Equipo CSV download | 30 |
| 38 | `components/equipos/UsuarioForm.tsx` | ADMIN create/edit user form | 55 |
| 39 | `components/equipos/UsuarioTable.tsx` | ADMIN user list table | 50 |

#### Estructura Components (5 files)

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 40 | `components/estructura/CarreraForm.tsx` | ABM carrera form | 45 |
| 41 | `components/estructura/CohorteForm.tsx` | ABM cohorte form | 45 |
| 42 | `components/estructura/ProgramaUploader.tsx` | File upload + metadata | 60 |
| 43 | `components/estructura/EvaluacionForm.tsx` | Evaluation date form | 45 |
| 44 | `components/estructura/EvaluacionCalendar.tsx` | Calendar view with markers | 60 |

#### Encuentros Components (6 files)

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 45 | `components/encuentros/EncuentroForm.tsx` | Single encounter create form | 45 |
| 46 | `components/encuentros/EncuentroRecurrenteForm.tsx` | Recurrent series config | 55 |
| 47 | `components/encuentros/EncuentroTable.tsx` | Transversal list with filters | 65 |
| 48 | `components/encuentros/EncuentroEditModal.tsx` | Inline edit + "apply to future" checkbox | 55 |
| 49 | `components/encuentros/ContenidoAulaPreview.tsx` | LMS content preview + copy | 50 |
| 50 | `components/encuentros/GuardiaTable.tsx` | Guardias list + register modal | 55 |

#### Coloquios Components (5 files)

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 51 | `components/coloquios/MetricasPanel.tsx` | 4 KPI cards | 45 |
| 52 | `components/coloquios/ConvocatoriaForm.tsx` | 3-step wizard form | 100 |
| 53 | `components/coloquios/ImportarAlumnosUploader.tsx` | CSV/XLSX upload + errors | 50 |
| 54 | `components/coloquios/ConvocatoriaTable.tsx` | List with metrics + pagination | 55 |
| 55 | `components/coloquios/ConvocatoriaDetail.tsx` | Detail view + reservations | 50 |

#### Tareas Components (5 files)

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 56 | `components/tareas/TareaCard.tsx` | My tasks card with status badge | 50 |
| 57 | `components/tareas/TareaForm.tsx` | Create/assign task form | 55 |
| 58 | `components/tareas/TareaTable.tsx` | Admin global table | 60 |
| 59 | `components/tareas/TareaCommentThread.tsx` | Comments timeline + input | 45 |
| 60 | `components/tareas/TareaStatusBadge.tsx` | State badge with color map | 25 |

#### Avisos Components (3 files)

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 61 | `components/avisos/AvisoForm.tsx` | Create/edit with markdown + all fields | 70 |
| 62 | `components/avisos/AvisoCard.tsx` | List card (severity badge, scope, dates) | 40 |
| 63 | `components/avisos/AvisoScopeSelector.tsx` | Global/materia/cohorte picker + roles | 50 |

#### Monitor Components (3 files)

| # | File | Purpose | Est. LOC |
|---|------|---------|----------|
| 64 | `components/monitor/MonitorGeneralTable.tsx` | Cross-tenant monitor table | 60 |
| 65 | `components/monitor/AuditoriaTable.tsx` | Activity audit log table | 55 |
| 66 | `components/monitor/MonitorFilters.tsx` | Shared filter bar (text, selects, date range) | 65 |

### Modified files

| # | File | Change |
|---|------|--------|
| 1 | `frontend/src/App.tsx` | Add imports for `CoordinacionLayout` + page components; insert `/coordinacion` route block under `<Route element={<Layout />}>` |
| 2 | `frontend/src/shared/components/Sidebar.tsx` | Replace existing `/equipos` entry with `/coordinacion/equipos`; add 6 new nav entries for estructura, encuentros, coloquios, tareas, avisos, monitor; add section header "Coordinación" |

**Total new files**: ~66 files
**Total modified files**: 2 files
**Estimated LOC**: ~3,500 (TSX + TS, excluding blanks and imports)

---

## 6. Key Types / Interfaces

```ts
// ── Equipos ──
interface Equipo {
  id: string;
  materia_id: string;
  materia_nombre: string;
  carrera_nombre: string;
  cohorte_nombre: string;
  roles: string[];
  fecha_desde: string;
  fecha_hasta: string;
  estado: 'activo' | 'inactivo';
}

interface Asignacion {
  id: string;
  docente_id: string;
  docente_nombre: string;
  materia_id: string;
  materia_nombre: string;
  carrera_id: string;
  cohorte_id: string;
  rol: string;
  fecha_desde: string;
  fecha_hasta: string;
  estado: string;
}

interface AsignacionRequest {
  docente_id: string;
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
  rol: string;
  fecha_desde: string;
  fecha_hasta: string;
}

interface AsignacionMasivaRequest extends Omit<AsignacionRequest, 'docente_id'> {
  docente_ids: string[];
}

interface UsuarioDocente {
  id: string;
  nombre: string;
  email: string;
  rol: string;
  regional: string;
  activo: boolean;
  ultima_actualizacion: string;
}

interface ClonarEquipoRequest {
  origen: { materia_id: string; cohorte_id: string };
  destino: { materia_id: string; cohorte_id: string };
}

// ── Estructura ──
interface Carrera {
  id: string;
  codigo: string;
  nombre: string;
  activa: boolean;
  creada: string;
}

interface Cohorte {
  id: string;
  nombre: string;        // "MAR-2025"
  year: number;
  fecha_desde: string;
  fecha_hasta: string;
  estado: string;
}

interface Programa {
  id: string;
  materia_id: string;
  materia_nombre: string;
  carrera_nombre: string;
  cohorte_nombre: string;
  titulo: string;
  filename: string;
  fecha_subida: string;
}

interface Evaluacion {
  id: string;
  materia_id: string;
  materia_nombre: string;
  cohorte_nombre: string;
  tipo: 'parcial' | 'tp' | 'coloquio';
  instancia: number;
  fecha: string;
  titulo: string;
}

// ── Encuentros ──
interface Encuentro {
  id: string;
  materia_id: string;
  materia_nombre: string;
  cohorte_nombre: string;
  docente_nombre: string;
  fecha: string;
  hora: string;
  titulo: string;
  estado: 'programado' | 'realizado' | 'cancelado';
  enlace?: string;
  grabacion?: string;
  comentario_interno?: string;
  es_recurrente: boolean;
  serie_id?: string;
}

interface SerieRecurrenteRequest {
  materia_id: string;
  dia_semana: number;       // 1-5 (lun-vie)
  horario: string;          // "18:00"
  fecha_inicio: string;
  semanas: number;           // 1-16
  titulo: string;
  enlace?: string;
}

interface Guardia {
  id: string;
  tutor_id: string;
  tutor_nombre: string;
  materia_nombre: string;
  dia: string;
  horario_desde: string;
  horario_hasta: string;
  estado: string;
  comentarios?: string;
}

// ── Coloquios ──
interface MetricasColoquios {
  total_alumnos_cargados: number;
  instancias_activas: number;
  reservas_activas: number;
  notas_registradas: number;
}

interface Convocatoria {
  id: string;
  materia_nombre: string;
  instancia: number;
  titulo: string;
  cohorte_nombre: string;
  dias: ConvocatoriaDia[];
  estado: string;
  alumnos_convocados: number;
  reservas_activas: number;
  cupos_libres: number;
}

interface ConvocatoriaDia {
  fecha: string;
  cupo_maximo: number;
}

// ── Tareas ──
type TareaEstado = 'pendiente' | 'en_proceso' | 'completada' | 'aprobada' | 'rechazada';

interface Tarea {
  id: string;
  titulo: string;
  descripcion: string;
  asignado_id: string;
  asignado_nombre: string;
  asignador_id: string;
  asignador_nombre: string;
  materia_id?: string;
  estado: TareaEstado;
  prioridad: 'baja' | 'media' | 'alta';
  fecha_limite?: string;
  fecha_creacion: string;
  comentarios: TareaComment[];
}

interface TareaComment {
  id: string;
  autor: string;
  contenido: string;
  fecha: string;
}

// ── Avisos ──
interface Aviso {
  id: string;
  titulo: string;
  cuerpo: string;
  alcance: 'global' | 'materia' | 'cohorte';
  roles_destinatarios: string[];
  severidad: 'informativo' | 'advertencia' | 'critico';
  estado: 'borrador' | 'publicado' | 'vencido';
  fecha_desde?: string;
  fecha_hasta?: string;
  requiere_ack: boolean;
  leidos_count?: number;
  total_destinatarios?: number;
}

// ── Monitor ──
interface MonitorFilters {
  nombre?: string;
  email?: string;
  comision?: string;
  regional?: string;
  materia?: string;
  actividad?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  q?: string;
}

interface MonitorEntry {
  alumno_id: string;
  nombre: string;
  email: string;
  comision: string;
  regional: string;
  materia: string;
  actividad: string;
  estado: string;
  ultima_actividad: string;
}

interface AuditoriaEntry {
  id: string;
  fecha_hora: string;
  docente_nombre: string;
  docente_rol: string;
  accion: string;
  materia_nombre: string;
  registros_afectados: number;
  ip: string;
  user_agent: string;
  detalle?: {
    request_payload?: string;
    response_status?: number;
    duracion_ms?: number;
  };
}
```

---

## 7. Testing Strategy

### Unit / component tests

Each component has a `.test.tsx` co-located next to it. Tests use vitest + @testing-library/react.

**Pattern per domain** (one test file per component):

```tsx
// features/coordinacion/components/equipos/__tests__/EquipoCard.test.tsx
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect } from 'vitest';

function renderWithProviders(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}
```

### What to test per component

| Component class | Tests |
|----------------|-------|
| **Forms** (AsignacionForm, CarreraForm, etc.) | Render all fields, submit empty (Zod validation), submit valid, error display, loading state |
| **Tables** (EquipoTable, ConvocatoriaTable, etc.) | Render data rows, empty state, loading skeleton, paginated data, column sorting |
| **Cards** (EquipoCard, AvisoCard, TareaCard) | Render with data, null/empty fields, status badge colors, overdue indicator |
| **Uploaders** (ProgramaUploader, ImportarAlumnosUploader) | File type validation, submit FormData, progress indicator, error display, partial error list |
| **Wizard** (ConvocatoriaForm) | Step forward/backward, data persistence across steps, step validation, final submit |
| **Layout** (CoordinacionLayout) | Renders sub-nav, active state, Outlet |
| **Monitor/Auditoria** | Filter integration (debounce), pagination, CSV export, empty results, expanded row detail |

### What NOT to test
- TanStack Query internals (testing library handles this)
- Axios interceptor behavior (tested once in shared)
- Permissions (tested once in PermissionGuard)
- Tailwind class correctness
- Navigation routing (integration-level)

### Coverage targets
- **≥80%** line coverage for components
- **≥90%** line coverage for hooks (edge cases: loading, error, empty data, invalidation logic)

---

## 8. Sidebar Update

```ts
// In Sidebar.tsx NAV_ITEMS:
const NAV_ITEMS: NavItem[] = [
  // ... existing items (Alumnos, Materias, Comisiones, Comunicación, Liquidaciones)

  // Replace existing Equipos entry
  { label: 'Equipos', path: '/coordinacion/equipos', icon: UsersRound, permission: 'equipos:ver' },

  // New coordinación entries
  { label: 'Estructura', path: '/coordinacion/estructura', icon: BookOpen, permission: 'estructura:gestionar' },
  { label: 'Encuentros', path: '/coordinacion/encuentros', icon: Calendar, permission: 'encuentros:ver' },
  { label: 'Coloquios', path: '/coordinacion/coloquios', icon: GraduationCap, permission: 'coloquios:ver' },
  { label: 'Tareas', path: '/coordinacion/tareas', icon: ClipboardCheck, permission: 'tareas:ver' },
  { label: 'Avisos', path: '/coordinacion/avisos', icon: Megaphone, permission: 'avisos:ver' },
  { label: 'Monitor', path: '/coordinacion/monitor', icon: Activity, permission: 'monitor:ver' },
];
```

The sidebar renders a section header "Coordinación" before these items to visually group them. Items are filtered by `can(permission)` — a user only sees entries they have permission for.

---

## 9. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Large scope (7 domains, 66 files)** | Long implementation time, coordination overhead | Each domain is self-contained; equips, estructura, encounters can be built in parallel. Coloquios (dependent on import and metrics) is the riskiest — start early. |
| **Coloquios wizard complexity** | UX confusion, state management bugs | Single FormData object lifted to wizard parent. Each step validates independently. Backward navigation preserves state. |
| **Recurrent instance generation latency** | User sees hanging progress | Fast path (synchronous response) handles most cases. Fallback to polling after 2s timeout. Show clear progress state. |
| **File validation mismatch (client vs server)** | User uploads valid file client-side but server rejects | Backend is the source of truth. Frontend gives early feedback (type, size) but server errors are displayed inline. |
| **Permission model mismatch** | User sees sidebar entry but gets 403 on API call | Sidebar entry gated by same permission. Backend enforces RBAC (fail-closed). 403 errors shown as inline permission errors. |
| **Stale data after cross-domain mutations** | E.g., editing equipo vigencia doesn't update encuentros view | Cross-domain invalidation is minimal by design. If needed, add `queryClient.invalidateQueries({ queryKey: ['coordinacion'] })` (broad) as a manual refresh button. |

---

## 10. Open Questions

| # | Question | Domain | Resolution needed from |
|---|----------|--------|----------------------|
| Q1 | `GET /api/v1/equipos/mis-equipos` — does this return the same shape as a filtered view of asignaciones, or is it a separate endpoint with a distinct response schema? | Equipos | Backend API spec (C-08) |
| Q2 | Convocatoria creation: does `POST /api/v1/coloquios` accept multiple days inline (array of `{fecha, cupo_maximo}`), or do days need separate sub-resource creation? | Coloquios | Backend API spec (C-16) |
| Q3 | Monitor general: is the endpoint paginated by default or returns all results? What's the default page size? | Monitor | Backend API spec (C-10/C-15 boundary) |
| Q4 | Aviso acknowledgment: is `POST /api/v1/avisos/{id}/ack` per-user (current session) or does it accept a `usuario_id` for admin bulk ack? | Avisos | Backend API spec (C-13) |
| Q5 | Are `icon` imports for new sidebar items (Calendar, GraduationCap, ClipboardCheck, Megaphone, Activity) available from the current lucide-react version? | Sidebar | Verify lucide-react v0.400+ availability |
