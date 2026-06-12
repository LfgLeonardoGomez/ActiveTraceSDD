import { NavLink, Outlet, useParams } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { AvisoCard } from '../components/avisos/AvisoCard';
import { AvisoForm } from '../components/avisos/AvisoForm';
import { useAvisos } from '../hooks/useAvisos';
import type { Aviso } from '../types/avisos.types';

const SUB_ROUTES = [
  { label: 'Listado', path: '/coordinacion/avisos', end: true },
  { label: '+ Nuevo aviso', path: '/coordinacion/avisos/nuevo' },
] as const;

export function AvisosLayout() {
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

export function AvisosList() {
  return <AvisoCard />;
}

export function CrearAviso() {
  return <AvisoForm />;
}

export function EditarAviso() {
  const { avisoId } = useParams<{ avisoId: string }>();
  const { data: avisos } = useAvisos();

  const aviso: Aviso | undefined = avisos?.find((a) => a.id === avisoId);

  if (!avisoId) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">ID de aviso no especificado</p>
      </div>
    );
  }

  if (!avisos) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  if (!aviso) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
        <p className="text-neutral-600">Aviso no encontrado</p>
      </div>
    );
  }

  return <AvisoForm aviso={aviso} />;
}
