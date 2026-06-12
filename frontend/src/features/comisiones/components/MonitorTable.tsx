import { Button } from '@/shared/components/ui/Button';
import type { MonitorEntry } from '../types/comisiones.types';

interface MonitorTableProps {
  data: MonitorEntry[];
  total: number;
  page: number;
  totalPages: number;
  isLoading: boolean;
  isError: boolean;
  onRefetch: () => void;
  onPageChange: (page: number) => void;
  esCoordinador?: boolean;
}

function estadoGeneral(actividades: MonitorEntry['estado_actividades']): { label: string; className: string } {
  if (actividades.length === 0) return { label: 'Sin datos', className: 'bg-neutral-100 text-neutral-600' };
  const aprobadas = actividades.filter((a) => a.aprobada).length;
  if (aprobadas === actividades.length) return { label: 'Al día', className: 'bg-success-50 text-success-700' };
  if (aprobadas === 0) return { label: 'Crítico', className: 'bg-danger-50 text-danger-700' };
  return { label: 'En riesgo', className: 'bg-warning-50 text-warning-700' };
}

export function MonitorTable({
  data,
  total,
  page,
  totalPages,
  isLoading,
  isError,
  onRefetch,
  onPageChange,
}: MonitorTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 animate-pulse rounded bg-neutral-200" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-md bg-danger-50 p-4 text-sm text-danger-600">
        <p>Error al cargar los datos de monitoreo</p>
        <button
          onClick={() => onRefetch()}
          className="mt-2 font-medium text-danger-700 underline hover:text-danger-800"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg border border-neutral-200 p-8 text-center">
        <p className="text-sm text-neutral-600">
          No se encontraron alumnos para los filtros seleccionados
        </p>
      </div>
    );
  }

  const from = (page - 1) * 50 + 1;
  const to = Math.min(page * 50, total);

  const ultimaActividad = (actividades: MonitorEntry['estado_actividades']): string => {
    if (actividades.length === 0) return '—';
    return actividades[actividades.length - 1].nombre;
  };

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-md border border-neutral-200">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Alumno
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Email
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Comisión
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Regional
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Actividad
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Estado
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Última actividad
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {data.map((entry) => {
              const estado = estadoGeneral(entry.estado_actividades);
              return (
                <tr key={entry.alumno_id} className="hover:bg-neutral-50">
                  <td className="px-3 py-2 font-medium text-neutral-900">{entry.nombre}</td>
                  <td className="px-3 py-2 text-neutral-600">{entry.email}</td>
                  <td className="px-3 py-2">{entry.comision}</td>
                  <td className="px-3 py-2">{entry.regional}</td>
                  <td className="px-3 py-2">
                    <span className="text-xs text-neutral-600">
                      {entry.estado_actividades.length} actividad
                      {entry.estado_actividades.length !== 1 ? 'es' : ''}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${estado.className}`}
                    >
                      {estado.label}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs text-neutral-600">
                    {ultimaActividad(entry.estado_actividades)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm text-neutral-600">
        <p>
          Mostrando {from}-{to} de {total} registros
        </p>
        <div className="flex items-center gap-2">
          <p className="text-xs">
            Página {page} de {totalPages}
          </p>
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Anterior
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Siguiente
          </Button>
        </div>
      </div>
    </div>
  );
}
