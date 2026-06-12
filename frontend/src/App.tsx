import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '@/shared/components/guards/ProtectedRoute';
import Layout from '@/shared/components/Layout';
import LoginPage from '@/features/auth/pages/LoginPage';
import TwoFactorPage from '@/features/auth/pages/TwoFactorPage';
import ForgotPasswordPage from '@/features/auth/pages/ForgotPasswordPage';
import ResetPasswordPage from '@/features/auth/pages/ResetPasswordPage';
import DashboardHome from '@/features/auth/pages/DashboardHome';

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
            {/* Future feature routes will go here */}
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
