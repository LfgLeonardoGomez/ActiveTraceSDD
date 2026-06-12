import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface TabNavProps {
  materiaId: string;
}

const TABS = [
  { label: 'Resumen', path: '' },
  { label: 'Importar', path: 'importar' },
  { label: 'Umbral', path: 'umbral' },
  { label: 'Atrasados', path: 'atrasados' },
  { label: 'Ranking', path: 'ranking' },
  { label: 'Notas Finales', path: 'notas-finales' },
  { label: 'TPs sin corregir', path: 'tps-sin-corregir' },
  { label: 'Monitor', path: 'monitor' },
  { label: 'Comunicaciones', path: 'comunicaciones' },
] as const;

export function TabNav({ materiaId }: TabNavProps) {
  return (
    <nav className="flex overflow-x-auto border-b border-neutral-200">
      {TABS.map((tab) => (
        <NavLink
          key={tab.path || 'index'}
          to={`/comisiones/${materiaId}/${tab.path}`}
          end={tab.path === ''}
          className={({ isActive }) =>
            cn(
              'whitespace-nowrap px-4 py-3 text-sm font-medium transition-colors',
              isActive
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-neutral-600 hover:text-neutral-900',
            )
          }
        >
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}
