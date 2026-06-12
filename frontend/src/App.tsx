import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '@/shared/components/guards/ProtectedRoute';
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
