import { NavLink, Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { usePermissions } from '@/shared/hooks/usePermissions';
import PermissionGuard from '@/shared/components/guards/PermissionGuard';
import { EquipoCard } from '../components/equipos/EquipoCard';
import { EquipoTable } from '../components/equipos/EquipoTable';
import { AsignacionForm } from '../components/equipos/AsignacionForm';
import { AsignacionMasivaForm } from '../components/equipos/AsignacionMasivaForm';
import { ClonarEquipoForm } from '../components/equipos/ClonarEquipoForm';
import { VigenciaEditor } from '../components/equipos/VigenciaEditor';
import { ExportButton } from '../components/equipos/ExportButton';
import { UsuarioTable } from '../components/equipos/UsuarioTable';

const SUB_ROUTES = [
  { label: 'Mis equipos', path: '/coordinacion/equipos', end: true },
  { label: 'Usuarios', path: '/coordinacion/equipos/usuarios', permission: 'usuarios:admin' },
  { label: 'Asignaciones', path: '/coordinacion/equipos/asignaciones' },
  { label: 'Asignación masiva', path: '/coordinacion/equipos/asignaciones/masiva' },
  { label: 'Clonar', path: '/coordinacion/equipos/clonar' },
  { label: 'Vigencia', path: '/coordinacion/equipos/vigencia' },
  { label: 'Exportar', path: '/coordinacion/equipos/exportar' },
] as const;

export function EquiposLayout() {
  const { can } = usePermissions();

  const visibleRoutes = SUB_ROUTES.filter(
    (r) => !('permission' in r) || !r.permission || can(r.permission),
  );

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

export function EquiposIndex() {
  return <EquipoCard />;
}

export function EquiposUsuarios() {
  return (
    <PermissionGuard requiredPermissions="usuarios:admin">
      <UsuarioTable />
    </PermissionGuard>
  );
}

export function EquiposAsignaciones() {
  return (
    <div className="space-y-6">
      <EquipoTable />
      <AsignacionForm />
    </div>
  );
}

export function EquiposAsignacionMasiva() {
  return <AsignacionMasivaForm />;
}

export function EquiposClonar() {
  return <ClonarEquipoForm />;
}

export function EquiposVigencia() {
  return <VigenciaEditor />;
}

export function EquiposExportar() {
  return <ExportButton />;
}
