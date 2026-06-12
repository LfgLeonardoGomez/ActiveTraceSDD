import { NavLink, Outlet, useParams } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Spinner } from '@/shared/components/ui/Spinner';
import { EncuentroTable } from '../components/encuentros/EncuentroTable';
import { EncuentroForm } from '../components/encuentros/EncuentroForm';
import { EncuentroRecurrenteForm } from '../components/encuentros/EncuentroRecurrenteForm';
import { EncuentroEditModal } from '../components/encuentros/EncuentroEditModal';
import { ContenidoAulaPreview } from '../components/encuentros/ContenidoAulaPreview';
import { GuardiaTable } from '../components/encuentros/GuardiaTable';
import { useEncuentros } from '../hooks/useEncuentros';

const SUB_ROUTES = [
  { label: 'Lista', path: '/coordinacion/encuentros', end: true },
  { label: 'Nuevo', path: '/coordinacion/encuentros/nuevo' },
  { label: 'Recurrente', path: '/coordinacion/encuentros/recurrente' },
  { label: 'Contenido Aula', path: '/coordinacion/encuentros/contenido-aula' },
  { label: 'Guardias', path: '/coordinacion/encuentros/guardias' },
] as const;

export function EncuentrosLayout() {
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

export function EncuentrosIndex() {
  return <EncuentroTable />;
}

export function EncuentrosNuevo() {
  return <EncuentroForm />;
}

export function EncuentrosRecurrente() {
  return <EncuentroRecurrenteForm />;
}

export function EncuentrosContenidoAula() {
  return <ContenidoAulaPreview />;
}

export function EncuentrosGuardias() {
  return <GuardiaTable />;
}

export function EncuentroEditPage() {
  const { encuentroId } = useParams<{ encuentroId: string }>();
  const { data: encuentros, isLoading } = useEncuentros();
  const encuentro = encuentros?.find((e) => e.id === encuentroId);

  if (!encuentroId) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">ID de encuentro no válido</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!encuentro) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
        <p className="text-neutral-600">Encuentro no encontrado</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-neutral-900">Editar Encuentro</h2>
        <p className="mt-1 text-sm text-neutral-500">{encuentro.materia} — {new Date(encuentro.fecha).toLocaleDateString()}</p>
      </div>
      <EncuentroEditModal
        encuentro={encuentro}
        onSuccess={() => window.history.back()}
        onClose={() => window.history.back()}
      />
    </div>
  );
}
