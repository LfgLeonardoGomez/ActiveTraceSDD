import { NavLink, Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';
import PermissionGuard from '@/shared/components/guards/PermissionGuard';
import { TareaCard } from '../components/tareas/TareaCard';
import { TareaTable } from '../components/tareas/TareaTable';
import { TareaForm } from '../components/tareas/TareaForm';

const SUB_ROUTES = [
  { label: 'Mis tareas', path: '/coordinacion/tareas', end: true },
  { label: 'Asignar', path: '/coordinacion/tareas/asignar' },
  { label: 'Admin', path: '/coordinacion/tareas/admin', permission: 'tareas:admin' },
] as const;

export function TareasLayout() {
  const visibleRoutes = SUB_ROUTES;

  return (
    <div className="flex flex-col gap-6">
      <nav className="flex overflow-x-auto border-b border-neutral-200">
        {visibleRoutes.map((route) => (
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

export function TareasIndex() {
  return <TareaCard />;
}

export function TareasAsignar() {
  return <TareaForm />;
}

export function TareasAdmin() {
  return (
    <PermissionGuard requiredPermissions="tareas:admin">
      <TareaTable />
    </PermissionGuard>
  );
}
