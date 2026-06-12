import { useState, useId } from 'react';
import { useNavigate } from 'react-router-dom';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useConvocatorias } from '../../hooks/useColoquios';
import type { Convocatoria } from '../../types/coloquios.types';

interface ConvocatoriaTableProps {
  filters?: Record<string, string>;
}

export function ConvocatoriaTable({ filters: externalFilters }: ConvocatoriaTableProps) {
  const tableId = useId();
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState<Record<string, string>>(externalFilters ?? {});
  const perPage = 25;

  const { data: convocatorias, isLoading, isError, refetch } = useConvocatorias(filters);

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex gap-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={`${tableId}-filter-sk-${i}`} className="h-9 w-40 animate-pulse rounded-md bg-neutral-200" />
          ))}
        </div>
        <div className="overflow-x-auto rounded-lg border border-neutral-200">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50">
              <tr>
                {['Materia', 'Instancia', 'Días disponibles', 'Convocados', 'Reservas activas', 'Cupos libres', 'Estado', 'Acciones'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={`${tableId}-row-sk-${i}`} className="animate-pulse border-t border-neutral-100">
                  {Array.from({ length: 8 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 w-20 rounded bg-neutral-200" />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">Error al cargar convocatorias</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!convocatorias || convocatorias.length === 0) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
        <p className="text-neutral-600">No hay convocatorias de coloquio</p>
        <button
          onClick={() => navigate('/coordinacion/coloquios/nuevo')}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Crear primera convocatoria
        </button>
      </div>
    );
  }

  const paginated = convocatorias.slice(page * perPage, (page + 1) * perPage);
  const totalPages = Math.ceil(convocatorias.length / perPage);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <input
          placeholder="Filtrar por materia..."
          className="h-9 rounded-md border border-neutral-300 px-3 text-sm"
          onChange={(e) => handleFilterChange('materia', e.target.value)}
        />
        <select
          className="h-9 rounded-md border border-neutral-300 px-3 text-sm"
          onChange={(e) => handleFilterChange('estado', e.target.value)}
          defaultValue=""
        >
          <option value="">Todos los estados</option>
          <option value="activa">Activa</option>
          <option value="cerrada">Cerrada</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded-lg border border-neutral-200">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50">
            <tr>
              {['Materia', 'Instancia', 'Días disponibles', 'Convocados', 'Reservas activas', 'Cupos libres', 'Estado', 'Acciones'].map((h) => (
                <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginated.map((c) => (
              <tr
                key={c.id}
                className="cursor-pointer border-t border-neutral-100 hover:bg-neutral-50"
                onClick={() => navigate(`/coordinacion/coloquios/${c.id}`)}
              >
                <td className="px-4 py-3 font-medium text-neutral-900">{c.materia}</td>
                <td className="px-4 py-3 text-neutral-700">{c.instancia}</td>
                <td className="px-4 py-3 text-neutral-700">{c.dias?.length ?? 0}</td>
                <td className="px-4 py-3 text-neutral-700">{c.total_convocados}</td>
                <td className="px-4 py-3 text-neutral-700">{c.reservas_activas}</td>
                <td className="px-4 py-3 text-neutral-700">{c.cupos_libres}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    c.estado === 'activa' ? 'bg-success-100 text-success-700' :
                    c.estado === 'cerrada' ? 'bg-neutral-100 text-neutral-600' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {c.estado}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={(e) => { e.stopPropagation(); navigate(`/coordinacion/coloquios/${c.id}`); }}
                    className="text-sm font-medium text-primary-600 hover:underline"
                  >
                    Ver
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-neutral-500">
            Mostrando {page * perPage + 1}–{Math.min((page + 1) * perPage, convocatorias.length)} de {convocatorias.length}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="rounded-md border border-neutral-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Anterior
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="rounded-md border border-neutral-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
