import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '@/shared/components/guards/ProtectedRoute';
import PermissionGuard from '@/shared/components/guards/PermissionGuard';
import Layout from '@/shared/components/Layout';
import LoginPage from '@/features/auth/pages/LoginPage';
import TwoFactorPage from '@/features/auth/pages/TwoFactorPage';
import ForgotPasswordPage from '@/features/auth/pages/ForgotPasswordPage';
import ResetPasswordPage from '@/features/auth/pages/ResetPasswordPage';
import DashboardHome from '@/features/auth/pages/DashboardHome';
import ComisionesPage from '@/features/comisiones/pages/ComisionesPage';
import ComisionDetailPage from '@/features/comisiones/pages/ComisionDetailPage';
import { ResumenTab } from '@/features/comisiones/components/ResumenTab';
import { ImportarTab } from '@/features/comisiones/components/ImportarTab';
import { UmbralTab } from '@/features/comisiones/components/UmbralTab';
import { AtrasadosTab } from '@/features/comisiones/components/AtrasadosTab';
import { RankingTab } from '@/features/comisiones/components/RankingTab';
import { NotasFinalesTab } from '@/features/comisiones/components/NotasFinalesTab';
import { TpsSinCorregirTab } from '@/features/comisiones/components/TpsSinCorregirTab';
import { MonitorTab } from '@/features/comisiones/components/MonitorTab';
import { ComunicacionesTab } from '@/features/comisiones/components/ComunicacionesTab';

import { CoordinacionLayout } from '@/features/coordinacion/components/CoordinacionLayout';
import CoordinacionHome from '@/features/coordinacion/pages/CoordinacionHome';
import {
  EquiposLayout,
  EquiposIndex,
  EquiposUsuarios,
  EquiposAsignaciones,
  EquiposAsignacionMasiva,
  EquiposClonar,
  EquiposVigencia,
  EquiposExportar,
} from '@/features/coordinacion/pages/EquiposPages';
import { EstructuraLayout } from '@/features/coordinacion/pages/EstructuraPages';
import { MonitorLayout, MonitorGeneral, MonitorAuditoria } from '@/features/coordinacion/pages/MonitorPages';
import { ColoquiosLayout } from '@/features/coordinacion/pages/ColoquiosPages';
import { TareasLayout, TareasIndex, TareasAsignar, TareasAdmin } from '@/features/coordinacion/pages/TareasPages';
import {
  EncuentrosLayout,
  EncuentrosIndex,
  EncuentrosNuevo,
  EncuentrosRecurrente,
  EncuentrosContenidoAula,
  EncuentrosGuardias,
  EncuentroEditPage,
} from '@/features/coordinacion/pages/EncuentrosPages';
import {
  AvisosLayout,
  AvisosList,
  CrearAviso,
  EditarAviso,
} from '@/features/coordinacion/pages/AvisosPages';

import LiquidacionesPage from '@/features/finanzas/pages/LiquidacionesPage';
import HistorialPage from '@/features/finanzas/pages/HistorialPage';
import SalarioGridPage from '@/features/finanzas/pages/SalarioGridPage';
import FacturasPage from '@/features/finanzas/pages/FacturasPage';

import EstructuraPage from '@/features/admin/pages/EstructuraPage';
import UsuariosPage from '@/features/admin/pages/UsuariosPage';
import AuditoriaPanelPage from '@/features/admin/pages/AuditoriaPanelPage';
import AuditoriaLogPage from '@/features/admin/pages/AuditoriaLogPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes — full screen, no layout */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/2fa" element={<TwoFactorPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Protected routes — wrapped in Layout */}
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<DashboardHome />} />
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

            <Route path="/coordinacion" element={<CoordinacionLayout />}>
              <Route index element={<CoordinacionHome />} />
              <Route path="equipos" element={<EquiposLayout />}>
                <Route index element={<EquiposIndex />} />
                <Route path="usuarios" element={<EquiposUsuarios />} />
                <Route path="asignaciones" element={<EquiposAsignaciones />} />
                <Route path="asignaciones/masiva" element={<EquiposAsignacionMasiva />} />
                <Route path="clonar" element={<EquiposClonar />} />
                <Route path="vigencia" element={<EquiposVigencia />} />
                <Route path="exportar" element={<EquiposExportar />} />
              </Route>
              <Route path="estructura/*" element={<EstructuraLayout />} />
              <Route path="encuentros" element={<EncuentrosLayout />}>
                <Route index element={<EncuentrosIndex />} />
                <Route path="nuevo" element={<EncuentrosNuevo />} />
                <Route path="recurrente" element={<EncuentrosRecurrente />} />
                <Route path="contenido-aula" element={<EncuentrosContenidoAula />} />
                <Route path="guardias" element={<EncuentrosGuardias />} />
                <Route path=":encuentroId/editar" element={<EncuentroEditPage />} />
              </Route>
              <Route path="coloquios/*" element={<ColoquiosLayout />} />
              <Route path="tareas" element={<TareasLayout />}>
                <Route index element={<TareasIndex />} />
                <Route path="asignar" element={<TareasAsignar />} />
                <Route path="admin" element={<TareasAdmin />} />
              </Route>
              <Route path="avisos" element={<AvisosLayout />}>
                <Route index element={<AvisosList />} />
                <Route path="nuevo" element={<CrearAviso />} />
                <Route path=":avisoId/editar" element={<EditarAviso />} />
              </Route>
              <Route path="monitor" element={<MonitorLayout />}>
                <Route index element={<MonitorGeneral />} />
                <Route path="auditoria" element={<MonitorAuditoria />} />
              </Route>
            </Route>

            {/* Finanzas */}
            <Route path="/finanzas" element={<PermissionGuard requiredPermissions="liquidaciones:ver" />}>
              <Route index element={<Navigate to="liquidaciones" replace />} />
              <Route path="liquidaciones" element={<LiquidacionesPage />} />
              <Route path="historial" element={<HistorialPage />} />
              <Route path="salarios" element={<PermissionGuard requiredPermissions="liquidaciones:configurar-salarios"><SalarioGridPage /></PermissionGuard>} />
              <Route path="facturas" element={<FacturasPage />} />
            </Route>

            {/* Admin */}
            <Route path="/admin" element={<PermissionGuard requiredPermissions={['estructura:gestionar', 'usuarios:gestionar', 'auditoria:ver']} requireAll={false} />}>
              <Route index element={<Navigate to="estructura" replace />} />
              <Route path="estructura" element={<PermissionGuard requiredPermissions="estructura:gestionar"><EstructuraPage /></PermissionGuard>} />
              <Route path="usuarios" element={<PermissionGuard requiredPermissions="usuarios:gestionar"><UsuariosPage /></PermissionGuard>} />
              <Route path="auditoria" element={<PermissionGuard requiredPermissions="auditoria:ver"><AuditoriaPanelPage /></PermissionGuard>} />
              <Route path="auditoria/log" element={<PermissionGuard requiredPermissions="auditoria:ver"><AuditoriaLogPage /></PermissionGuard>} />
            </Route>
          </Route>
        </Route>

        {/* 404 */}
        <Route
          path="*"
          element={
            <div className="flex min-h-screen items-center justify-center">
              <div className="text-center">
                <h1 className="text-4xl font-bold text-neutral-900">404</h1>
                <p className="mt-2 text-muted-foreground">Página no encontrada</p>
              </div>
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
