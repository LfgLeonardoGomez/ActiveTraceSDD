# Tasks: C-24 Frontend Finanzas y Admin

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~3,800–4,200 (code + tests) |
| 400-line budget risk | High |
| 800-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Setup + Finanzas) → PR 2 (Admin) → PR 3 (Integration + Tests) |
| Delivery strategy | single-pr |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Setup + Finanzas (types, services, hooks, liquidaciones, salarios, facturas) | PR 1 | Self-contained; no admin deps; ~1,600 lines |
| 2 | Admin (estructura, usuarios, auditoría with charts) | PR 2 | Targets PR 1 branch or main; ~1,600 lines |
| 3 | Integration + shared + full test suite | PR 3 | Routes, sidebar, KPICard, SegmentTabs; ~800 lines |

## Phase 1: Setup

- [x] 1.1 Add `recharts` to `frontend/package.json` dependencies
- [x] 1.2 Create `features/finanzas/types/` — `liquidaciones.types.ts`, `salarios.types.ts`, `facturas.types.ts` with Zod schemas + TS interfaces per design §Contracts
- [x] 1.3 Create `features/admin/types/` — `estructura.types.ts`, `usuarios.types.ts`, `auditoria.types.ts` with Zod schemas + TS interfaces per design §Contracts
- [x] 1.4 Create `features/finanzas/services/` — `liquidaciones.api.ts`, `salarios.api.ts`, `facturas.api.ts` wrapping Axios calls per design §TanStack Query Mapping
- [x] 1.5 Create `features/admin/services/` — `estructura.api.ts`, `usuarios.api.ts`, `auditoria.api.ts` wrapping Axios calls per design §TanStack Query Mapping
- [x] 1.6 Create `features/finanzas/hooks/useLiquidaciones.ts`, `useSalarios.ts`, `useFacturas.ts` — TanStack Query hooks with cache invalidation per design
- [x] 1.7 Create `features/admin/hooks/useEstructuraAdmin.ts`, `useUsuarios.ts`, `useAuditoria.ts` — TanStack Query hooks per design

## Phase 2: Finanzas — Liquidaciones

- [x] 2.1 Create `features/finanzas/components/liquidaciones/PeriodoSelector.tsx` — cohorte select + month input
- [x] 2.2 Create `shared/components/KPICard.tsx` — reusable metric card (title, value, delta, format)
- [x] 2.3 Create `features/finanzas/components/liquidaciones/KpiCards.tsx` — renders KPICard ×2 for total_sin/con_factura
- [x] 2.4 Create `shared/components/SegmentTabs.tsx` — General/NEXO/Facturantes tab switcher
- [x] 2.5 Create `features/finanzas/components/liquidaciones/SegmentedTable.tsx` — table with subtotals per segment
- [x] 2.6 Create `features/finanzas/components/liquidaciones/CierreDialog.tsx` — confirmation modal; validates R3 (disable after close)
- [x] 2.7 Create `features/finanzas/components/liquidaciones/TeacherDetail.tsx` — teacher breakdown panel (R5)
- [x] 2.8 Create `features/finanzas/pages/LiquidacionesPage.tsx` — assemble PeriodoSelector + KpiCards + SegmentTabs + SegmentedTable + CierreDialog
- [x] 2.9 Create `features/finanzas/pages/HistorialPage.tsx` — closed liquidations list with filters (R4)

## Phase 3: Finanzas — Grilla Salarial

- [x] 3.1 Create `features/finanzas/components/salarios/SalarioBaseTable.tsx` — ABM table with role/amount/vigencia columns
- [x] 3.2 Create `features/finanzas/components/salarios/SalarioBaseForm.tsx` — create/edit form with Zod validation
- [x] 3.3 Create `features/finanzas/components/salarios/SalarioPlusTable.tsx` — ABM table with group/role/amount/vigencia
- [x] 3.4 Create `features/finanzas/components/salarios/SalarioPlusForm.tsx` — create/edit form with Zod validation
- [x] 3.5 Create `features/finanzas/components/salarios/VigenciaConflictAlert.tsx` — inline overlap warning (R3)
- [x] 3.6 Create `features/finanzas/pages/SalarioGridPage.tsx` — tabs for Base/Plus, filter by role (R4)

## Phase 4: Finanzas — Facturas

- [x] 4.1 Create `features/finanzas/components/facturas/FacturaTable.tsx` — invoice list with status badges (R1)
- [x] 4.2 Create `features/finanzas/components/facturas/FacturaDetail.tsx` — metadata panel: file, payment date (R3)
- [x] 4.3 Create `features/finanzas/components/facturas/AbonarButton.tsx` — status toggle Pendiente→Abonada (R2)
- [x] 4.4 Create `features/finanzas/pages/FacturasPage.tsx` — assemble table + detail + filters

## Phase 5: Admin — Estructura

- [x] 5.1 Create `features/admin/components/estructura/CarreraTable.tsx` + `CarreraForm.tsx` — CRUD with toggle estado (R1)
- [x] 5.2 Create `features/admin/components/estructura/CohorteTable.tsx` + `CohorteForm.tsx` — CRUD with anio/vigencia (R2)
- [x] 5.3 Create `features/admin/components/estructura/MateriaTable.tsx` + `MateriaForm.tsx` — CRUD with toggle (R3)
- [x] 5.4 Create `features/admin/pages/EstructuraPage.tsx` — tabs Carreras/Cohortes/Materias + name/estado filters (R4)

## Phase 6: Admin — Usuarios

- [x] 6.1 Create `features/admin/components/usuarios/UsuarioTable.tsx` — user list with roles badges (R1, R4)
- [x] 6.2 Create `features/admin/components/usuarios/UsuarioDetail.tsx` — slide-over panel: DNI, CUIL, CBU, banco, regional (R2)
- [x] 6.3 Create `features/admin/components/usuarios/UsuarioForm.tsx` — edit form: nombre, email, regional, banco, estado (R3)
- [x] 6.4 Create `features/admin/pages/UsuariosPage.tsx` — assemble table + detail + form

## Phase 7: Admin — Auditoría

- [x] 7.1 Create `features/admin/components/auditoria/ChartSkeleton.tsx` — loading placeholder
- [x] 7.2 Create `features/admin/components/auditoria/ScopeBadge.tsx` — "Vista personal" for COORDINADOR (R5)
- [x] 7.3 Create `features/admin/components/auditoria/AccionesPorDiaChart.tsx` — Recharts LineChart, lazy-loaded (R1)
- [x] 7.4 Create `features/admin/components/auditoria/ComunicacionesChart.tsx` — Recharts StackedBarChart, lazy-loaded (R2)
- [x] 7.5 Create `features/admin/components/auditoria/InteraccionesChart.tsx` — Recharts BarChart, lazy-loaded (R3)
- [x] 7.6 Create `features/admin/components/auditoria/LogFilters.tsx` — date range, action, user, materia, estado (R4)
- [x] 7.7 Create `features/admin/components/auditoria/LogTable.tsx` — paginated audit log (R4)
- [x] 7.8 Create `features/admin/pages/AuditoriaPanelPage.tsx` — KPIs + 3 lazy charts + recent actions
- [x] 7.9 Create `features/admin/pages/AuditoriaLogPage.tsx` — filters + log table

## Phase 8: Integration & Testing

- [x] 8.1 Create `features/finanzas/test/setup.ts` + `features/admin/test/setup.ts` — mock AuthContext, usePermissions, api (follow coordinacion/test/setup.ts pattern)
- [x] 8.2 Write component tests: KpiCards, SegmentTabs, CierreDialog, VigenciaConflictAlert, ScopeBadge, SalarioBaseForm, CarreraForm, UsuarioForm
- [x] 8.3 Write hook tests: useLiquidaciones, useSalarios, useFacturas, useAuditoria — mock MSW handlers
- [x] 8.4 Write page integration tests: LiquidacionesPage, SalarioGridPage, AuditoriaPanelPage — QueryClientProvider + BrowserRouter + MSW
- [x] 8.5 Update `App.tsx` — add `/finanzas/*` and `/admin/*` routes with PermissionGuard wrappers per design §Route Design
- [x] 8.6 Update `Sidebar.tsx` — add FINANZAS and ADMIN sections with permission-conditional rendering per design §Sidebar Integration
