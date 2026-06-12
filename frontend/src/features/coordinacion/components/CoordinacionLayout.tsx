import { NavLink, Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';

const DOMAINS = [
  { label: 'Inicio', path: '/coordinacion', end: true },
  { label: 'Equipos', path: '/coordinacion/equipos' },
  { label: 'Estructura', path: '/coordinacion/estructura' },
  { label: 'Encuentros', path: '/coordinacion/encuentros' },
  { label: 'Coloquios', path: '/coordinacion/coloquios' },
  { label: 'Tareas', path: '/coordinacion/tareas' },
  { label: 'Avisos', path: '/coordinacion/avisos' },
  { label: 'Monitor', path: '/coordinacion/monitor' },
] as const;

export function CoordinacionLayout() {
  return (
    <div className="flex flex-col gap-6">
      <nav className="flex overflow-x-auto border-b border-neutral-200">
        {DOMAINS.map((domain) => (
          <NavLink
            key={domain.path}
            to={domain.path}
            end={domain.end ?? false}
            className={({ isActive }) =>
              cn(
                'whitespace-nowrap px-4 py-3 text-sm font-medium transition-colors',
                isActive
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-neutral-600 hover:text-neutral-900',
              )
            }
          >
            {domain.label}
          </NavLink>
        ))}
      </nav>

      <div className="flex-1">
        <Outlet />
      </div>
    </div>
  );
}
