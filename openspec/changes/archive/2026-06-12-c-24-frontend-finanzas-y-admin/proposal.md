# Proposal: C-24 Frontend Finanzas y Admin

## Intent

Provide frontend UI for two distinct feature areas that consume already-functional backend APIs:

1. **FINANZAS** — Liquidation period view with segmented breakdown (general/NEXO/facturante), KPIs, close flow, salary grid ABM, invoice management, and liquidation history.
2. **ADMIN** — Academic structure management (careers, cohorts, subjects), tenant user management, audit panel with filters and charts, and full audit log with canonical filters.

Both areas have role-based visibility: FINANZAS sees finanzas, ADMIN sees admin, COORDINADOR sees audit read-only with `is_propio` scope.

## Scope

### In Scope
- Feature module `features/finanzas/` — liquidation views, salary grid ABM, invoice management
- Feature module `features/admin/` — academic structure, users, audit panel, audit log
- TanStack Query hooks, Zod schemas, API service files for both features
- Sidebar navigation updates for FINANZAS and ADMIN sections
- Role-based route guards using `PermissionGuard` (existing pattern)
- KPI summary cards for liquidation (total_sin_factura, total_con_factura)
- Segmented liquidation table (general, NEXO, facturantes)
- Audit panel charts (actions-by-day, communications-by-status, interactions-by-category)
- Reusable chart component wrapper (using Recharts as chart library)
- Unit/integration tests for key components and hooks

### Out of Scope
- Any backend work (APIs already exist per C-18, C-19, C-06, C-07)
- Profile editing, messaging (C-20)
- Communication/bulk email features (C-12)
- Dashboard home widget redesign
- Mobile-specific responsive layouts (desktop-first, standard responsive)

## Capabilities

### New Capabilities
- `finanzas-ui`: Liquidation period view, close flow, salary grid ABM, invoice management, liquidation history
- `admin-ui`: Academic structure (carreras, cohortes, materias), tenant users, audit panel with charts, audit log with filters

### Modified Capabilities
- `auth-shell`: Sidebar navigation extended with Finanzas and Admin sections (route + permission changes only)

## Approach

### Module Split: Two Separate Feature Modules

Split into `features/finanzas/` and `features/admin/` rather than a monolithic `finanzas-admin/`. Rationale:
- FINANZAS and ADMIN serve different user roles (FINANZAS vs ADMIN)
- Different permission guards, different sidebar sections
- Independent deployment/testing — changes in finanzas don't require touching admin code
- Matches existing pattern (coordinacion, comisiones are separate)

Each module follows the established structure:
```
features/{name}/
  ├── components/     # PascalCase React components
  ├── hooks/          # TanStack Query hooks (useXyz.ts)
  ├── pages/          # Route-level page components
  ├── services/       # API client files (xyz.api.ts)
  └── types/          # Zod schemas + TypeScript types (xyz.types.ts)
```

### Finance Feature (`features/finanzas/`)

**Pages:**
- `LiquidacionesPage` — period selector (cohorte + month), segmented table, KPI cards
- `LiquidacionDetailPage` — detailed view of a single period with close action
- `HistorialPage` — closed liquidations list with filters
- `SalarioGridPage` — ABM for SalarioBase and SalarioPlus with vigencia
- `FacturasPage` — invoice list with upload, status toggle, filters

**Component breakdown:**
- `SegmentedTable` — renders 3 segments (general, NEXO, facturantes) with subtotals
- `KpiCards` — total_sin_factura, total_con_factura summary
- `PeriodoSelector` — cohorte dropdown + month picker
- `CierreDialog` — confirmation modal for liquidation close
- `SalarioBaseTable`, `SalarioPlusTable` — ABM tables with vigencia editing
- `FacturaTable` — invoice list with status badges and filters
- `FacturaUploadForm` — file upload + metadata form for new invoices

**API endpoints consumed:**
- `GET /api/liquidaciones/{cohorte_id}/{periodo}` — liquidation view
- `POST /api/liquidaciones/{cohorte_id}/{periodo}/cerrar` — close
- `GET /api/liquidaciones/historial` — closed periods
- `GET/POST/PATCH/DELETE /api/liquidaciones/salario-base` — SalarioBase ABM
- `GET/POST/PATCH/DELETE /api/liquidaciones/salario-plus` — SalarioPlus ABM
- `GET/POST/DELETE /api/facturas` + `POST /api/facturas/{id}/abonar` — invoices
- `GET/POST/PATCH/DELETE /api/liquidaciones/materia-grupo-plus` — materia-to-group mapping

### Admin Feature (`features/admin/`)

**Pages:**
- `EstructuraPage` — tabs for carreras, cohortes, materias (reuses C-23's EstructuraLayout pattern)
- `UsuariosPage` — tenant user list with role management
- `AuditoriaPanelPage` — KPIs, 3 chart sections
- `AuditoriaLogPage` — filterable log table with_pagination

**Component breakdown:**
- Reuses `MonitorFilters` pattern from coordinacion for audit filters
- `AccionesPorDiaChart`, `ComunicacionesChart`, `InteraccionesChart` — Recharts wrappers
- `UltimasAccionesTable` — recent actions with configurable limit
- `LogTable` — paginated audit log with canonical filters
- `LogFilters` — date range, action code, usuario, materia, estado
- `CarreraForm`, `CohorteForm`, `MateriaForm` — admin ABM forms
- `UsuarioTable`, `UsuarioForm` — user management (extends C-07 patterns)

**API endpoints consumed:**
- `GET /api/auditoria/panel/acciones-por-dia` — actions-by-day chart
- `GET /api/auditoria/panel/comunicaciones-por-docente` — communications by status
- `GET /api/auditoria/panel/interacciones-por-docente-materia` — interactions
- `GET /api/auditoria/panel/ultimas-acciones` — recent actions
- `GET /api/auditoria/catalogo-acciones` — action catalog for filter dropdown
- `GET /api/auditoria/log` — full audit log with pagination
- `GET/POST/PATCH/* /api/admin/carreras` — carrera CRUD
- `GET/POST/PATCH/* /api/admin/cohortes` — cohorte CRUD
- `GET/POST/PATCH/* /api/admin/materias` — materia CRUD
- `GET/POST/PATCH/* /api/admin/usuarios` — user CRUD

### Chart Library Decision: Recharts

Install `recharts` as the chart library. Rationale:
- React-native, TypeScript-friendly, MIT-licensed
- Lightweight for the chart types needed (line chart, bar chart, stacked bar)
- Industry standard for React dashboards
- No existing chart dependency in the project

### Role-Based Visibility

Sidebar navigation uses existing `usePermissions` + `can()` pattern:
- **FINANZAS section**: visible when `can('liquidaciones:ver')`
  - Liquidaciones: `liquidaciones:ver`
  - Salarios: `liquidaciones:configurar-salarios`
  - Facturas: `facturas:ver`
- **ADMIN section**: visible when `can('estructura:gestionar')` OR `can('usuarios:gestionar')` OR `can('auditoria:ver')`
  - Estructura: `estructura:gestionar`
  - Usuarios: `usuarios:gestionar`
  - Auditoría: `auditoria:ver`

`PermissionGuard` wraps each route section, redirecting to `/` on unauthorized access.

### Key Reuse from Existing Features

- `MonitorFilters` pattern → `LogFilters` for audit log
- `PaginatedResponse<T>` type → reuse across finanzas and admin APIs
- `usePermissions` hook → role-based visibility
- `PermissionGuard` component → route-level guards
- API client pattern (`api.ts` + interceptors) → feature API files
- Dashboard CRUD page skill → standardized layout for admin CRUD pages

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/features/finanzas/` | New | Liquidation, salary grid, invoice modules |
| `frontend/src/features/admin/` | New | Structure, users, audit modules |
| `frontend/src/shared/components/Sidebar.tsx` | Modified | Add FINANZAS and ADMIN nav sections |
| `frontend/src/App.tsx` | Modified | Add finance and admin routes |
| `frontend/src/shared/hooks/usePermissions.ts` | Unchanged | Already used for visibility |
| `frontend/package.json` | Modified | Add recharts dependency |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Recharts bundle size (~120KB gzipped) | Low | Lazy-load audit panel page components; tree-shake unused chart types |
| Liquidation close is irreversible (409 on double-close) | Medium | UI confirmation dialog with period display; disable button after close; refresh on mutation success |
| Salary grid vigencia overlap validation requires UX clarity | Medium | Show date-range conflicts inline; precompute vigencia gaps in UI |
| Audit panel scope `(propio)` for COORDINADOR may confuse users | Low | Show scope badge ("Vista personal" vs "Vista completa") in the panel header |
| Admin structure endpoints may differ from coordinacion's existing `estructura.api.ts` | Medium | Map both to same shared types; admin uses `/api/admin/*` routes, coordinacion uses `/api/v1/estructura/*` — verify both work |

## Rollback Plan

1. Remove `recharts` from `package.json`
2. Remove `features/finanzas/` and `features/admin/` directories
3. Revert Sidebar and App.tsx to remove FINANZAS and ADMIN routes
4. No database changes or backend dependencies — pure frontend removal

## Dependencies

- C-18 (liquidaciones-y-honorarios) — backend APIs for liquidations, salary grid, invoices ✓
- C-19 (panel-auditoria-metricas) — backend APIs for audit panel and log ✓
- C-06 (estructura-academica) — backend APIs for carreras, cohortes, materias ✓
- C-07 (usuarios-y-asignaciones) — backend APIs for user management ✓
- C-21 (frontend-shell-y-auth) — auth, layout, sidebar, route guards ✓
- `recharts` npm package — to install

## Success Criteria

- [ ] FINANZAS user can view segmented liquidation table with KPIs for a period
- [ ] FINANZAS user can close a liquidation period with confirmation dialog
- [ ] FINANZAS user can manage SalarioBase and SalarioPlus with vigencia validation
- [ ] FINANZAS user can list, upload, and mark invoices as abonada
- [ ] ADMIN user can CRUD carreras, cohortes, materias
- [ ] ADMIN user can view and manage tenant users
- [ ] ADMIN/FINANZAS user can view audit panel with charts and filtered log
- [ ] COORDINADOR sees only own audit data (propio scope)
- [ ] Sidebar shows correct sections based on role permissions
- [ ] Chart components lazy-load and render correctly
- [ ] All forms validate with Zod schemas (extra='forbid')