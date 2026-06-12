import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { useAuth } from '@/shared/services/AuthContext';
import api from '@/shared/services/api';
import { Button } from '@/shared/components/ui/Button';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isStoppingImpersonation, setIsStoppingImpersonation] = useState(false);
  const { user } = useAuth();

  const stopImpersonation = async () => {
    setIsStoppingImpersonation(true);
    try {
      await api.post('/api/auth/impersonation/stop');
      window.location.reload();
    } catch {
      setIsStoppingImpersonation(false);
    }
  };

  return (
    <div className="flex h-screen">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex flex-1 flex-col lg:pl-64">
        <Topbar onToggleSidebar={() => setSidebarOpen((prev) => !prev)} />

        {/* Impersonation banner */}
        {user?.is_impersonating && (
          <div className="flex items-center justify-between bg-warning-100 px-6 py-2 text-sm text-warning-600">
            <span>
              Estás operando como {user.nombre} {user.apellido}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={stopImpersonation}
              isLoading={isStoppingImpersonation}
              className="text-warning-600 hover:bg-warning-200"
            >
              Salir de impersonación
            </Button>
          </div>
        )}

        <main className="flex-1 overflow-y-auto bg-neutral-50 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
