import { useState } from 'react';
import { NavLink, Outlet, useLocation, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/lib/utils';
import { usePermissions } from '@/shared/hooks/usePermissions';
import PermissionGuard from '@/shared/components/guards/PermissionGuard';
import { MetricasPanel } from '../components/coloquios/MetricasPanel';
import { ConvocatoriaTable } from '../components/coloquios/ConvocatoriaTable';
import { ConvocatoriaForm } from '../components/coloquios/ConvocatoriaForm';
import { ConvocatoriaDetail } from '../components/coloquios/ConvocatoriaDetail';
import { useConvocatoriaAdmin } from '../hooks/useColoquios';
import { Spinner } from '@/shared/components/ui/Spinner';
import { getReservasActivas } from '../services/coloquios.api';
import type { Reserva } from '../types/coloquios.types';

const SUB_ROUTES = [
  { label: 'Dashboard', path: '/coordinacion/coloquios', end: true },
  { label: 'Nuevo', path: '/coordinacion/coloquios/nuevo' },
  { label: 'Admin', path: '/coordinacion/coloquios/admin', permission: 'coloquios:admin' },
] as const;

export function ColoquiosLayout() {
  const { can } = usePermissions();
  const location = useLocation();

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
        {location.pathname === '/coordinacion/coloquios' && <ColoquiosDashboard />}
        {location.pathname === '/coordinacion/coloquios/nuevo' && <CrearConvocatoria />}
        {location.pathname.startsWith('/coordinacion/coloquios/admin') && (
          <PermissionGuard requiredPermissions="coloquios:admin">
            <ColoquiosAdmin />
          </PermissionGuard>
        )}
        {location.pathname.match(/^\/coordinacion\/coloquios\/(?!nuevo|admin)[a-f0-9-]+$/) && (
          <ConvocatoriaDetail />
        )}
      </div>
    </div>
  );
}

function ColoquiosDashboard() {
  return (
    <div className="space-y-8">
      <MetricasPanel />
      <ConvocatoriaTable />
    </div>
  );
}

function CrearConvocatoria() {
  return <ConvocatoriaForm />;
}

function ColoquiosAdmin() {
  const [tab, setTab] = useState<'convocatorias' | 'registro' | 'reservas'>('convocatorias');
  const [selectedConvocatoria, setSelectedConvocatoria] = useState<string>('');
  const { data: convocatorias, isLoading, isError, refetch } = useConvocatoriaAdmin();

  const { data: reservas, isLoading: reservasLoading } = useQuery({
    queryKey: ['coordinacion', 'coloquios', 'reservas-activas'],
    queryFn: getReservasActivas,
    enabled: tab === 'reservas',
  });

  const tabs = [
    { key: 'convocatorias' as const, label: 'Convocatorias' },
    { key: 'registro' as const, label: 'Registro académico' },
    { key: 'reservas' as const, label: 'Reservas activas' },
  ];

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex gap-1">
          {tabs.map((t) => (
            <div key={t.key} className="h-9 w-32 animate-pulse rounded-t-md bg-neutral-200" />
          ))}
        </div>
        <div className="h-64 animate-pulse rounded-lg bg-neutral-100" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">Error al cargar datos de administración</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-neutral-900">Administración de coloquios</h2>

      <div className="flex gap-1 border-b border-neutral-200">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              'rounded-t-md px-4 py-2 text-sm font-medium transition-colors',
              tab === t.key
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-neutral-600 hover:text-neutral-900',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'convocatorias' && (
        <div className="overflow-x-auto rounded-lg border border-neutral-200">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50">
              <tr>
                {['Materia', 'Instancia', 'Título', 'Estado', 'Convocados', 'Reservas', 'Acciones'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(!convocatorias || convocatorias.length === 0) ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-neutral-500">
                    No hay convocatorias registradas
                  </td>
                </tr>
              ) : (
                convocatorias.map((c) => (
                  <tr key={c.id} className="border-t border-neutral-100">
                    <td className="px-4 py-3 font-medium text-neutral-900">{c.materia}</td>
                    <td className="px-4 py-3 text-neutral-700">{c.instancia}</td>
                    <td className="px-4 py-3 text-neutral-700">{c.titulo}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        c.estado === 'activa' ? 'bg-success-100 text-success-700' : 'bg-neutral-100 text-neutral-600'
                      }`}>
                        {c.estado}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-neutral-700">{c.total_convocados}</td>
                    <td className="px-4 py-3 text-neutral-700">{c.reservas_activas}</td>
                    <td className="px-4 py-3">
                      <button className="text-sm font-medium text-primary-600 hover:underline">
                        Cerrar
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'registro' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-neutral-700">Convocatoria</label>
            <select
              value={selectedConvocatoria}
              onChange={(e) => setSelectedConvocatoria(e.target.value)}
              className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm"
            >
              <option value="">Seleccioná una convocatoria</option>
              {(convocatorias ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.materia} — Instancia {c.instancia}
                </option>
              ))}
            </select>
          </div>

          {!selectedConvocatoria ? (
            <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
              <p className="text-neutral-600">Seleccioná una convocatoria para ver el registro académico</p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-neutral-200">
              <table className="w-full text-sm">
                <thead className="bg-neutral-50">
                  <tr>
                    {['Alumno', 'Documento', 'Nota', 'Estado'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-neutral-500">
                      No hay registros académicos para esta convocatoria
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'reservas' && (
        <div className="overflow-x-auto rounded-lg border border-neutral-200">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50">
              <tr>
                {['Alumno', 'Convocatoria', 'Día', 'Horario', 'Estado'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {reservasLoading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-neutral-500">
                    Cargando reservas...
                  </td>
                </tr>
              ) : !reservas || reservas.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-neutral-500">
                    No hay reservas activas
                  </td>
                </tr>
              ) : (
                reservas.map((r) => (
                  <tr key={r.id} className="border-t border-neutral-100">
                    <td className="px-4 py-3 font-medium text-neutral-900">{r.alumno}</td>
                    <td className="px-4 py-3 text-neutral-700">{r.convocatoria_id}</td>
                    <td className="px-4 py-3 text-neutral-700">{r.dia}</td>
                    <td className="px-4 py-3 text-neutral-700">{r.horario}</td>
                    <td className="px-4 py-3">
                      <span className="rounded-full bg-success-100 px-2 py-0.5 text-xs font-medium text-success-700">
                        {r.estado}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function ColoquiosIndex() {
  return <ColoquiosDashboard />;
}
