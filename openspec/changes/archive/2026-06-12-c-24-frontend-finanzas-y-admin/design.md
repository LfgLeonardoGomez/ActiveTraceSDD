# Design: C-24 Frontend Finanzas y Admin

## Technical Approach

Implement two independent feature modules — `features/finanzas/` and `features/admin/` — consuming already-built backend APIs (C-18, C-19, C-06, C-07). Both follow the established `coordinacion` pattern: feature-based directory structure, TanStack Query hooks wrapping Axios services, Zod-validated forms via React Hook Form, and Tailwind-styled components. Recharts is added as the chart library for audit panel visualizations.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|---|---|---|---|
| Module split | `features/finanzas/` + `features/admin/` | Single `features/finanzas-admin/` | Different roles, permissions, and sidebar sections; independent deploy/testing |
| Chart library | Recharts | Chart.js, D3 | React-native, TypeScript-friendly, MIT license, standard for React dashboards |
| Route layout | Nested routes under `/finanzas/*` and `/admin/*` | Flat routes | Matches existing `coordinacion/*` pattern; keeps URL hierarchy readable |
| Sidebar nav | Conditional sections via `usePermissions` | Backend-driven nav | Keeps auth purely frontend; `can()` pattern already exists |
| Data fetching | TanStack Query + Axios | SWR, fetch | Already used across `comisiones` and `coordinacion`; consistent cache invalidation |
| Form validation | Zod + React Hook Form | Yup, Valibot | Zod already in dependencies; `extra='forbid'` aligns with hard rules |
| Lazy loading | `React.lazy` for audit charts | Eager load | Recharts is ~120KB gzipped; lazy-load reduces initial bundle |

## Data Flow

```
User Action
    ↓
React Component (Page/Component)
    ↓
TanStack Query Hook (useXyz.ts)
    ↓
Axios Service (xyz.api.ts) ──→ Backend API
    ↓
Zod Schema / TypeScript Types
    ↓
Component re-render with data
```

Cache invalidation: mutations call `queryClient.invalidateQueries({ queryKey: [...] })` following the `coordinacion` pattern.

## File Changes

### New Files

| File | Description |
|------|-------------|
| `frontend/src/features/finanzas/components/liquidaciones/SegmentedTable.tsx` | Three-segment table (General/NEXO/Facturantes) |
| `frontend/src/features/finanzas/components/liquidaciones/KpiCards.tsx` | `total_sin_factura` / `total_con_factura` cards |
| `frontend/src/features/finanzas/components/liquidaciones/PeriodoSelector.tsx` | Cohorte + month picker |
| `frontend/src/features/finanzas/components/liquidaciones/CierreDialog.tsx` | Close confirmation modal |
| `frontend/src/features/finanzas/components/liquidaciones/TeacherDetail.tsx` | Teacher-level breakdown panel |
| `frontend/src/features/finanzas/components/salarios/SalarioBaseTable.tsx` | ABM table for SalarioBase |
| `frontend/src/features/finanzas/components/salarios/SalarioBaseForm.tsx` | Create/edit form with vigencia |
| `frontend/src/features/finanzas/components/salarios/SalarioPlusTable.tsx` | ABM table for SalarioPlus |
| `frontend/src/features/finanzas/components/salarios/SalarioPlusForm.tsx` | Create/edit form with group + vigencia |
| `frontend/src/features/finanzas/components/salarios/VigenciaConflictAlert.tsx` | Inline overlap warning |
| `frontend/src/features/finanzas/components/facturas/FacturaTable.tsx` | Invoice list with status badges |
| `frontend/src/features/finanzas/components/facturas/FacturaDetail.tsx` | Metadata panel (file, payment date) |
| `frontend/src/features/finanzas/components/facturas/AbonarButton.tsx` | Status toggle to Abonada |
| `frontend/src/features/finanzas/pages/LiquidacionesPage.tsx` | Period selector + segmented table + KPIs |
| `frontend/src/features/finanzas/pages/HistorialPage.tsx` | Closed liquidations list with filters |
| `frontend/src/features/finanzas/pages/SalarioGridPage.tsx` | Tabs for SalarioBase / SalarioPlus ABM |
| `frontend/src/features/finanzas/pages/FacturasPage.tsx` | Invoice list with filters |
| `frontend/src/features/finanzas/hooks/useLiquidaciones.ts` | Query/mutation hooks for liquidation APIs |
| `frontend/src/features/finanzas/hooks/useSalarios.ts` | Query/mutation hooks for SalarioBase/Plus |
| `frontend/src/features/finanzas/hooks/useFacturas.ts` | Query/mutation hooks for invoice APIs |
| `frontend/src/features/finanzas/services/liquidaciones.api.ts` | Axios calls for liquidation endpoints |
| `frontend/src/features/finanzas/services/salarios.api.ts` | Axios calls for salary grid endpoints |
| `frontend/src/features/finanzas/services/facturas.api.ts` | Axios calls for invoice endpoints |
| `frontend/src/features/finanzas/types/liquidaciones.types.ts` | TypeScript interfaces + Zod schemas |
| `frontend/src/features/finanzas/types/salarios.types.ts` | TypeScript interfaces + Zod schemas |
| `frontend/src/features/finanzas/types/facturas.types.ts` | TypeScript interfaces + Zod schemas |
| `frontend/src/features/admin/components/estructura/CarreraForm.tsx` | Admin-level carrera CRUD form |
| `frontend/src/features/admin/components/estructura/CohorteForm.tsx` | Admin-level cohorte CRUD form |
| `frontend/src/features/admin/components/estructura/MateriaForm.tsx` | Admin-level materia CRUD form |
| `frontend/src/features/admin/components/estructura/CarreraTable.tsx` | Admin carrera list with toggle |
| `frontend/src/features/admin/components/estructura/CohorteTable.tsx` | Admin cohorte list with toggle |
| `frontend/src/features/admin/components/estructura/MateriaTable.tsx` | Admin materia list with toggle |
| `frontend/src/features/admin/components/usuarios/UsuarioTable.tsx` | Tenant user list with roles |
| `frontend/src/features/admin/components/usuarios/UsuarioForm.tsx` | Edit user form (nombre, email, estado, etc.) |
| `frontend/src/features/admin/components/usuarios/UsuarioDetail.tsx` | DNI, CUIL, CBU, banco, regional panel |
| `frontend/src/features/admin/components/auditoria/AccionesPorDiaChart.tsx` | Line chart (lazy-loaded) |
| `frontend/src/features/admin/components/auditoria/ComunicacionesChart.tsx` | Stacked bar chart (lazy-loaded) |
| `frontend/src/features/admin/components/auditoria/InteraccionesChart.tsx` | Bar chart (lazy-loaded) |
| `frontend/src/features/admin/components/auditoria/LogTable.tsx` | Paginated audit log table |
| `frontend/src/features/admin/components/auditoria/LogFilters.tsx` | Date range, action, user, materia, estado filters |
| `frontend/src/features/admin/components/auditoria/ScopeBadge.tsx` | "Vista personal" badge for COORDINADOR |
| `frontend/src/features/admin/components/auditoria/ChartSkeleton.tsx` | Loading placeholder for charts |
| `frontend/src/features/admin/pages/EstructuraPage.tsx` | Tabs for Carreras / Cohortes / Materias |
| `frontend/src/features/admin/pages/UsuariosPage.tsx` | User list + detail panel |
| `frontend/src/features/admin/pages/AuditoriaPanelPage.tsx` | KPIs + 3 chart sections + recent actions |
| `frontend/src/features/admin/pages/AuditoriaLogPage.tsx` | Filterable log table |
| `frontend/src/features/admin/hooks/useEstructuraAdmin.ts` | Query/mutation hooks for admin structure |
| `frontend/src/features/admin/hooks/useUsuarios.ts` | Query/mutation hooks for user management |
| `frontend/src/features/admin/hooks/useAuditoria.ts` | Query/mutation hooks for audit panel/log |
| `frontend/src/features/admin/services/estructura.api.ts` | Axios calls for `/api/admin/carreras`, etc. |
| `frontend/src/features/admin/services/usuarios.api.ts` | Axios calls for `/api/admin/usuarios` |
| `frontend/src/features/admin/services/auditoria.api.ts` | Axios calls for `/api/auditoria/*` |
| `frontend/src/features/admin/types/estructura.types.ts` | Admin estructura types + Zod schemas |
| `frontend/src/features/admin/types/usuarios.types.ts` | User types + Zod schemas |
| `frontend/src/features/admin/types/auditoria.types.ts` | Audit types + Zod schemas |
| `frontend/src/shared/components/KPICard.tsx` | Reusable metric card (title, value, delta) |
| `frontend/src/shared/components/SegmentTabs.tsx` | General / NEXO / Facturante tab switcher |
| `frontend/src/features/finanzas/test/setup.ts` | Feature-level test mocks (vi.mock) |
| `frontend/src/features/admin/test/setup.ts` | Feature-level test mocks (vi.mock) |

### Modified Files

| File | Change |
|------|--------|
| `frontend/src/App.tsx` | Add `/finanzas/*` and `/admin/*` routes with `PermissionGuard` wrappers |
| `frontend/src/shared/components/Sidebar.tsx` | Add FINANZAS and ADMIN navigation sections with permission checks |
| `frontend/package.json` | Add `recharts` to `dependencies` |
| `frontend/vite.config.ts` (if needed) | Ensure `recharts` is not externalized |

### Deleted Files

None.

## Component Tree

### Finanzas

```
LiquidacionesPage
├── PeriodoSelector
│   └── cohorte select + month input
├── KpiCards
│   └── KPICard (x2)
├── SegmentTabs
│   ├── "General" → SegmentedTable (general data)
│   ├── "NEXO" → SegmentedTable (nexo data)
│   └── "Facturantes" → SegmentedTable (facturantes data)
└── CierreDialog (conditional, open only)

HistorialPage
├── FilterBar (reused pattern)
└── PaginatedTable (closed periods)

SalarioGridPage
├── TabNav: "Salario Base" | "Salario Plus"
│   ├── SalarioBaseTable → SalarioBaseForm (modal/inline)
│   └── SalarioPlusTable → SalarioPlusForm (modal/inline)
└── VigenciaConflictAlert (inline, when overlap detected)

FacturasPage
├── FilterBar
├── FacturaTable
│   ├── StatusBadge
│   └── AbonarButton (conditional)
└── FacturaDetail (slide-over / modal)
```

### Admin

```
EstructuraPage
├── TabNav: "Carreras" | "Cohortes" | "Materias"
│   ├── CarreraTable → CarreraForm (modal/inline)
│   ├── CohorteTable → CohorteForm (modal/inline)
│   └── MateriaTable → MateriaForm (modal/inline)
└── FilterBar (name + estado)

UsuariosPage
├── UsuarioTable
│   └── UsuarioDetail (slide-over)
└── UsuarioForm (modal, edit only)

AuditoriaPanelPage
├── ScopeBadge (if COORDINADOR + propio)
├── KPICard (x2-3 summary metrics)
├── React.Suspense + lazy
│   ├── AccionesPorDiaChart (LineChart)
│   ├── ComunicacionesChart (StackedBarChart)
│   └── InteraccionesChart (BarChart)
└── UltimasAccionesTable (recent actions)

AuditoriaLogPage
├── LogFilters
└── LogTable (paginated)
```

## Data Flow — TanStack Query Mapping

### Finanzas

| UI Feature | Hook | Query Key | Backend Endpoint | Method | Cache Invalidation |
|---|---|---|---|---|---|
| View liquidation | `useLiquidacion(cohorteId, periodo)` | `['finanzas', 'liquidacion', cohorteId, periodo]` | `GET /api/liquidaciones/{cohorte_id}/{periodo}` | Query | — |
| Close period | `useCerrarLiquidacion()` | — | `POST /api/liquidaciones/{cohorte_id}/{periodo}/cerrar` | Mutation | Invalidate `['finanzas', 'liquidacion', ...]` and `['finanzas', 'historial']` |
| Historial list | `useHistorial(filters)` | `['finanzas', 'historial', filters]` | `GET /api/liquidaciones/historial` | Query | — |
| SalarioBase list | `useSalarioBase()` | `['finanzas', 'salario-base']` | `GET /api/liquidaciones/salario-base` | Query | — |
| Create SalarioBase | `useCrearSalarioBase()` | — | `POST /api/liquidaciones/salario-base` | Mutation | Invalidate `['finanzas', 'salario-base']` |
| Update SalarioBase | `useActualizarSalarioBase()` | — | `PATCH /api/liquidaciones/salario-base/{id}` | Mutation | Invalidate `['finanzas', 'salario-base']` |
| Delete SalarioBase | `useEliminarSalarioBase()` | — | `DELETE /api/liquidaciones/salario-base/{id}` | Mutation | Invalidate `['finanzas', 'salario-base']` |
| SalarioPlus list | `useSalarioPlus()` | `['finanzas', 'salario-plus']` | `GET /api/liquidaciones/salario-plus` | Query | — |
| Create SalarioPlus | `useCrearSalarioPlus()` | — | `POST /api/liquidaciones/salario-plus` | Mutation | Invalidate `['finanzas', 'salario-plus']` |
| Update SalarioPlus | `useActualizarSalarioPlus()` | — | `PATCH /api/liquidaciones/salario-plus/{id}` | Mutation | Invalidate `['finanzas', 'salario-plus']` |
| Delete SalarioPlus | `useEliminarSalarioPlus()` | — | `DELETE /api/liquidaciones/salario-plus/{id}` | Mutation | Invalidate `['finanzas', 'salario-plus']` |
| Invoice list | `useFacturas(filters)` | `['finanzas', 'facturas', filters]` | `GET /api/facturas` | Query | — |
| Upload invoice | `useCrearFactura()` | — | `POST /api/facturas` | Mutation | Invalidate `['finanzas', 'facturas']` |
| Mark paid | `useAbonarFactura()` | — | `POST /api/facturas/{id}/abonar` | Mutation | Invalidate `['finanzas', 'facturas']` |
| Delete invoice | `useEliminarFactura()` | — | `DELETE /api/facturas/{id}` | Mutation | Invalidate `['finanzas', 'facturas']` |

### Admin

| UI Feature | Hook | Query Key | Backend Endpoint | Method | Cache Invalidation |
|---|---|---|---|---|---|
| Carreras list | `useCarrerasAdmin()` | `['admin', 'carreras']` | `GET /api/admin/carreras` | Query | — |
| Create Carrera | `useCrearCarreraAdmin()` | — | `POST /api/admin/carreras` | Mutation | Invalidate `['admin', 'carreras']` |
| Update Carrera | `useActualizarCarreraAdmin()` | — | `PATCH /api/admin/carreras/{id}` | Mutation | Invalidate `['admin', 'carreras']` |
| Cohortes list | `useCohortesAdmin()` | `['admin', 'cohortes']` | `GET /api/admin/cohortes` | Query | — |
| Create Cohorte | `useCrearCohorteAdmin()` | — | `POST /api/admin/cohortes` | Mutation | Invalidate `['admin', 'cohortes']` |
| Update Cohorte | `useActualizarCohorteAdmin()` | — | `PATCH /api/admin/cohortes/{id}` | Mutation | Invalidate `['admin', 'cohortes']` |
| Materias list | `useMateriasAdmin()` | `['admin', 'materias']` | `GET /api/admin/materias` | Query | — |
| Create Materia | `useCrearMateriaAdmin()` | — | `POST /api/admin/materias` | Mutation | Invalidate `['admin', 'materias']` |
| Update Materia | `useActualizarMateriaAdmin()` | — | `PATCH /api/admin/materias/{id}` | Mutation | Invalidate `['admin', 'materias']` |
| User list | `useUsuariosAdmin()` | `['admin', 'usuarios']` | `GET /api/admin/usuarios` | Query | — |
| Update User | `useActualizarUsuarioAdmin()` | — | `PATCH /api/admin/usuarios/{id}` | Mutation | Invalidate `['admin', 'usuarios']` |
| Actions chart | `useAccionesPorDia()` | `['admin', 'auditoria', 'acciones-por-dia']` | `GET /api/auditoria/panel/acciones-por-dia` | Query | — |
| Communications chart | `useComunicacionesPorDocente()` | `['admin', 'auditoria', 'comunicaciones']` | `GET /api/auditoria/panel/comunicaciones-por-docente` | Query | — |
| Interactions chart | `useInteraccionesPorDocenteMateria()` | `['admin', 'auditoria', 'interacciones']` | `GET /api/auditoria/panel/interacciones-por-docente-materia` | Query | — |
| Recent actions | `useUltimasAcciones()` | `['admin', 'auditoria', 'ultimas-acciones']` | `GET /api/auditoria/panel/ultimas-acciones` | Query | — |
| Audit log | `useAuditLog(filters)` | `['admin', 'auditoria', 'log', filters]` | `GET /api/auditoria/log` | Query | — |
| Action catalog | `useCatalogoAcciones()` | `['admin', 'auditoria', 'catalogo']` | `GET /api/auditoria/catalogo-acciones` | Query | — |

## Interfaces / Contracts

### Zod Schemas (excerpt)

```typescript
// features/finanzas/types/liquidaciones.types.ts
import { z } from 'zod';

export const PeriodoSchema = z.object({
  cohorte_id: z.string().uuid(),
  mes: z.string().regex(/^\d{4}-\d{2}$/),
});

export const CerrarLiquidacionSchema = z.object({
  confirmado: z.literal(true),
});

export const LiquidacionItemSchema = z.object({
  docente_id: z.string().uuid(),
  docente_nombre: z.string(),
  rol: z.string(),
  salario_base: z.number().nonnegative(),
  salario_plus: z.number().nonnegative(),
  comisiones: z.number().nonnegative(),
  total: z.number().nonnegative(),
  es_facturante: z.boolean().optional(),
  es_nexo: z.boolean().optional(),
});

export const LiquidacionViewSchema = z.object({
  periodo: z.string(),
  estado: z.enum(['abierto', 'cerrado']),
  segmento_general: z.array(LiquidacionItemSchema),
  segmento_nexo: z.array(LiquidacionItemSchema),
  segmento_facturantes: z.array(LiquidacionItemSchema),
  total_sin_factura: z.number().nonnegative(),
  total_con_factura: z.number().nonnegative(),
});

export type LiquidacionView = z.infer<typeof LiquidacionViewSchema>;

// features/finanzas/types/salarios.types.ts
export const SalarioBaseSchema = z.object({
  id: z.string().uuid(),
  rol: z.string(),
  monto: z.number().positive(),
  vigencia_desde: z.string().date(),
  vigencia_hasta: z.string().date(),
}).strict();

export const SalarioPlusSchema = z.object({
  id: z.string().uuid(),
  grupo: z.string(),
  rol: z.string(),
  monto: z.number().positive(),
  vigencia_desde: z.string().date(),
  vigencia_hasta: z.string().date(),
}).strict();

// features/admin/types/auditoria.types.ts
export const AuditLogFiltersSchema = z.object({
  fecha_desde: z.string().date().optional(),
  fecha_hasta: z.string().date().optional(),
  accion: z.string().optional(),
  usuario_id: z.string().uuid().optional(),
  materia_id: z.string().uuid().optional(),
  estado: z.string().optional(),
  page: z.number().int().positive().default(1),
  page_size: z.number().int().positive().default(50),
}).strict();
```

### TypeScript Types

```typescript
// features/finanzas/types/liquidaciones.types.ts
export interface LiquidacionItem {
  docente_id: string;
  docente_nombre: string;
  rol: string;
  salario_base: number;
  salario_plus: number;
  comisiones: number;
  total: number;
  es_facturante?: boolean;
  es_nexo?: boolean;
}

export interface LiquidacionView {
  periodo: string;
  estado: 'abierto' | 'cerrado';
  segmento_general: LiquidacionItem[];
  segmento_nexo: LiquidacionItem[];
  segmento_facturantes: LiquidacionItem[];
  total_sin_factura: number;
  total_con_factura: number;
}

// features/finanzas/types/facturas.types.ts
export interface Factura {
  id: string;
  docente_id: string;
  docente_nombre: string;
  periodo: string;
  monto: number;
  estado: 'pendiente' | 'abonada' | 'cancelada';
  fecha_subida: string;
  fecha_pago?: string;
  archivo_url?: string;
}

// features/admin/types/auditoria.types.ts
export interface AccionPorDia {
  fecha: string;
  cantidad: number;
}

export interface ComunicacionPorDocente {
  docente_id: string;
  docente_nombre: string;
  enviadas: number;
  pendientes: number;
  fallidas: number;
}

export interface InteraccionPorDocenteMateria {
  docente_id: string;
  docente_nombre: string;
  materia_id: string;
  materia_nombre: string;
  interacciones: number;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  usuario_id: string;
  usuario_nombre: string;
  accion: string;
  modulo: string;
  descripcion: string;
  materia_id?: string;
  materia_nombre?: string;
  estado: string;
}
```

## Route Design

```tsx
// App.tsx additions (inside <Route element={<Layout />}>)

import PermissionGuard from '@/shared/components/guards/PermissionGuard';

// Finanzas
import LiquidacionesPage from '@/features/finanzas/pages/LiquidacionesPage';
import HistorialPage from '@/features/finanzas/pages/HistorialPage';
import SalarioGridPage from '@/features/finanzas/pages/SalarioGridPage';
import FacturasPage from '@/features/finanzas/pages/FacturasPage';

// Admin
import EstructuraPage from '@/features/admin/pages/EstructuraPage';
import UsuariosPage from '@/features/admin/pages/UsuariosPage';
import AuditoriaPanelPage from '@/features/admin/pages/AuditoriaPanelPage';
import AuditoriaLogPage from '@/features/admin/pages/AuditoriaLogPage';

// Inside protected layout routes:
<Route path="/finanzas" element={<PermissionGuard requiredPermissions="liquidaciones:ver" />}>
  <Route index element={<Navigate to="liquidaciones" replace />} />
  <Route path="liquidaciones" element={<LiquidacionesPage />} />
  <Route path="historial" element={<HistorialPage />} />
  <Route path="salarios" element={<PermissionGuard requiredPermissions="liquidaciones:configurar-salarios"><SalarioGridPage /></PermissionGuard>} />
  <Route path="facturas" element={<FacturasPage />} />
</Route>

<Route path="/admin" element={<PermissionGuard requiredPermissions={['estructura:gestionar', 'usuarios:gestionar', 'auditoria:ver']} requireAll={false} />}>
  <Route index element={<Navigate to="estructura" replace />} />
  <Route path="estructura" element={<PermissionGuard requiredPermissions="estructura:gestionar"><EstructuraPage /></PermissionGuard>} />
  <Route path="usuarios" element={<PermissionGuard requiredPermissions="usuarios:gestionar"><UsuariosPage /></PermissionGuard>} />
  <Route path="auditoria" element={<PermissionGuard requiredPermissions="auditoria:ver"><AuditoriaPanelPage /></PermissionGuard>} />
  <Route path="auditoria/log" element={<PermissionGuard requiredPermissions="auditoria:ver"><AuditoriaLogPage /></PermissionGuard>} />
</Route>
```

## Sidebar Integration

Add two new sections to `Sidebar.tsx`:

```tsx
const FINANZAS_ITEMS: NavItem[] = [
  { label: 'Liquidaciones', path: '/finanzas/liquidaciones', icon: DollarSign, permission: 'liquidaciones:ver' },
  { label: 'Salarios', path: '/finanzas/salarios', icon: DollarSign, permission: 'liquidaciones:configurar-salarios' },
  { label: 'Facturas', path: '/finanzas/facturas', icon: DollarSign, permission: 'facturas:ver' },
];

const ADMIN_ITEMS: NavItem[] = [
  { label: 'Estructura', path: '/admin/estructura', icon: BookOpen, permission: 'estructura:gestionar' },
  { label: 'Usuarios', path: '/admin/usuarios', icon: Users, permission: 'usuarios:gestionar' },
  { label: 'Auditoría', path: '/admin/auditoria', icon: Activity, permission: 'auditoria:ver' },
];
```

Render them after the Coordinación section, conditional on `some((item) => can(item.permission))`.

## Shared Components

### Reuse from Existing Features

| Component | Source | Used In |
|---|---|---|
| `Card`, `CardHeader`, `CardContent`, `CardTitle` | `shared/components/ui/Card.tsx` | All pages |
| `Button`, `Spinner`, `Input`, `Label` | `shared/components/ui/*.tsx` | All forms |
| `PermissionGuard` | `shared/components/guards/PermissionGuard.tsx` | Route wrappers |
| `usePermissions` | `shared/hooks/usePermissions.ts` | Sidebar, conditional UI |
| `useDebounce` | `shared/hooks/useDebounce.ts` | Filter inputs |
| `api` | `shared/services/api.ts` | All service files |
| `MonitorFilters` pattern | `coordinacion/components/monitor/MonitorFilters.tsx` | `LogFilters` design |
| `EstructuraLayout` pattern | `coordinacion/pages/EstructuraPages.tsx` | `EstructuraPage` tabs |

### New Shared Components

| Component | Props | Description |
|---|---|---|
| `KPICard` | `{ title: string; value: number; delta?: number; format?: 'currency' \| 'number' }` | Metric summary card with optional delta indicator |
| `SegmentTabs` | `{ segments: { key: string; label: string; count?: number }[]; active: string; onChange: (key) => void }` | Tab switcher for General / NEXO / Facturantes |

`AuditChart` is NOT a new shared component — each chart is a small Recharts wrapper rendered directly in the audit page with `React.lazy` and `React.Suspense`. No abstraction needed for three chart types.

## Testing Strategy

| Layer | What | Approach |
|---|---|---|
| Unit — Components | `CierreDialog`, `KpiCards`, `SegmentTabs`, `VigenciaConflictAlert`, `ScopeBadge` | `@testing-library/react` + `vitest`; render + userEvent + assert visibility |
| Unit — Forms | `SalarioBaseForm`, `CarreraForm`, `UsuarioForm` | Fill inputs, submit, assert Zod validation errors, assert mutation called |
| Unit — Hooks | `useLiquidaciones`, `useAuditoria`, `useUsuariosAdmin` | `renderHook` from `@testing-library/react`; mock `msw` handlers for API calls |
| Integration — Page | `LiquidacionesPage`, `AuditoriaPanelPage` | Render with `QueryClientProvider` + `BrowserRouter`; mock API with `msw`; assert data renders |
| E2E | (Optional) Liquidation close flow | `playwright` — not in scope for this change unless explicitly requested |

**Test Setup**: Each feature module (`finanzas`, `admin`) includes its own `test/setup.ts` that mocks `AuthContext`, `usePermissions`, and `api` — following the `coordinacion/test/setup.ts` pattern.

**Coverage target**: ≥80% lines for new code; ≥90% for business rule paths (close flow, vigencia overlap, scope badge logic).

## Migration / Rollout

No data migration required. Pure frontend change.

Rollout steps:
1. Install `recharts` dependency
2. Merge feature modules
3. Update Sidebar and App.tsx routes
4. Smoke-test each route with FINANZAS and ADMIN roles
5. Verify COORDINADOR sees propio-scoped audit data
6. Verify 403 redirect when accessing routes without permission

## Open Questions

- [ ] Do we need a `MateriaGrupoPlus` mapping UI in this change? The proposal mentions `GET/POST/PATCH/DELETE /api/liquidaciones/materia-grupo-plus` but the specs don't explicitly list it. If needed, add a sub-page under `SalarioGridPage`.
- [ ] Should `FacturaUploadForm` support drag-and-drop file upload? The spec only mentions "upload" — standard file input is sufficient unless UX requests otherwise.
- [ ] Do admin estructura endpoints (`/api/admin/*`) support soft-delete toggle or hard delete? The spec says "toggle estado" — verify backend returns `409` on duplicate codes (reuse CarreraForm conflict handling).
- [ ] Is there a `liquidaciones:configurar-salarios` permission in the backend RBAC catalog? The proposal references it; verify it exists before routing.
