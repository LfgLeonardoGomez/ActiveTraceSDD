import { useState, useId } from 'react';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useAsignaciones } from '../../hooks/useEquipos';

export function EquipoTable() {
  const tableId = useId();
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const perPage = 25;

  const { data: asignaciones, isLoading, isError, refetch } = useAsignaciones(filters);

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={`${tableId}-filter-skeleton-${i}`} className="h-9 w-32 animate-pulse rounded-md bg-neutral-200" />
          ))}
        </div>
        <div className="overflow-x-auto rounded-lg border border-neutral-200">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50">
              <tr>
                {['Docente', 'Materia', 'Carrera', 'Cohorte', 'Rol', 'Vigencia', 'Estado'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={`${tableId}-row-skeleton-${i}`} className="animate-pulse border-t border-neutral-100">
                  {Array.from({ length: 7 }).map((_, j) => (
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
        <p className="text-danger-600">Error al cargar asignaciones</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!asignaciones || asignaciones.length === 0) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
        <p className="text-neutral-600">No hay asignaciones registradas</p>
        <p className="mt-1 text-sm text-neutral-500">Creá la primera asignación para comenzar</p>
      </div>
    );
  }

  const paginated = asignaciones.slice(page * perPage, (page + 1) * perPage);
  const totalPages = Math.ceil(asignaciones.length / perPage);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <input
          placeholder="Buscar docente..."
          className="h-9 rounded-md border border-neutral-300 px-3 text-sm"
          onChange={(e) => handleFilterChange('docente', e.target.value)}
        />
        <input
          placeholder="Materia..."
          className="h-9 rounded-md border border-neutral-300 px-3 text-sm"
          onChange={(e) => handleFilterChange('materia', e.target.value)}
        />
        <input
          placeholder="Rol..."
          className="h-9 rounded-md border border-neutral-300 px-3 text-sm"
          onChange={(e) => handleFilterChange('rol', e.target.value)}
        />
      </div>

      <div className="overflow-x-auto rounded-lg border border-neutral-200">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50">
            <tr>
              {['Docente', 'Materia', 'Carrera', 'Cohorte', 'Rol', 'Vigencia', 'Estado'].map((h) => (
                <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginated.map((a) => (
              <tr key={a.id} className="border-t border-neutral-100 hover:bg-neutral-50">
                <td className="px-4 py-3 font-medium text-neutral-900">{a.docente}</td>
                <td className="px-4 py-3 text-neutral-700">{a.materia}</td>
                <td className="px-4 py-3 text-neutral-700">{a.carrera}</td>
                <td className="px-4 py-3 text-neutral-700">{a.cohorte}</td>
                <td className="px-4 py-3 text-neutral-700">{a.rol}</td>
                <td className="px-4 py-3 text-neutral-700">{a.fecha_desde} — {a.fecha_hasta}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    a.estado === 'activo' ? 'bg-success-100 text-success-700' : 'bg-neutral-100 text-neutral-600'
                  }`}>
                    {a.estado}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-neutral-500">
            Mostrando {page * perPage + 1}–{Math.min((page + 1) * perPage, asignaciones.length)} de {asignaciones.length}
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
