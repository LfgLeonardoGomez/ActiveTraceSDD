import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { MonitorFilters } from '../components/monitor/MonitorFilters';
import { MonitorGeneralTable } from '../components/monitor/MonitorGeneralTable';
import { AuditoriaTable } from '../components/monitor/AuditoriaTable';
import type { MonitorFilters as Filters } from '../types/monitor.types';

const SUB_ROUTES = [
  { label: 'General', path: '/coordinacion/monitor', end: true },
  { label: 'Auditoría', path: '/coordinacion/monitor/auditoria' },
] as const;

export function MonitorLayout() {
  return (
    <div className="flex flex-col gap-6">
      <nav className="flex overflow-x-auto border-b border-neutral-200">
        {SUB_ROUTES.map((route) => (
          <NavLink
            key={route.path}
            to={route.path}
            end={'end' in route ? route.end : false}
            className={({ isActive }) =>
              cn(
                'whitespace-nowrap px-4 py-3 text-sm font-medium transition-colors',
                isActive
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-neutral-600 hover:text-neutral-900',
              )
            }
          >
            {route.label}
          </NavLink>
        ))}
      </nav>

      <div className="flex-1">
        <Outlet />
      </div>
    </div>
  );
}

export function MonitorGeneral() {
  const [filters, setFilters] = useState<Filters>({});
  const [page, setPage] = useState(1);

  const handleFiltersChange = (newFilters: Filters) => {
    setFilters(newFilters);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-neutral-900">Monitor general</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Visualizá el estado de todos los alumnos, sus actividades y última interacción
        </p>
      </div>

      <MonitorFilters
        mode="general"
        isLoading={false}
        onFiltersChange={handleFiltersChange}
      />

      <MonitorGeneralTable filters={filters} page={page} onPageChange={setPage} />
    </div>
  );
}

export function MonitorAuditoria() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-neutral-900">Auditoría</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Registro detallado de todas las acciones realizadas en el sistema
        </p>
      </div>

      <AuditoriaTable />
    </div>
  );
}
