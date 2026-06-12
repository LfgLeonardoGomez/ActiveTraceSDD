import { useState, useId, useCallback } from 'react';
import { useMonitorGeneral } from '../../hooks/useMonitorCoordinacion';
import type { MonitorFilters, MonitorEntry } from '../../types/monitor.types';

const PER_PAGE = 50;

function csvEscape(val: string | null | undefined): string {
  if (val == null) return '';
  const s = String(val);
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function exportToCsv(rows: MonitorEntry[], filename: string) {
  const headers = ['Alumno', 'Email', 'Comisión', 'Regional', 'Materia', 'Actividad', 'Estado', 'Última actividad'];
  const lines = rows.map((r) =>
    [r.nombre, r.email, r.comision, r.regional, r.materia, r.actividad, r.estado, r.ultima_actividad]
      .map(csvEscape)
      .join(','),
  );
  const csv = [headers.join(','), ...lines].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

interface MonitorGeneralTableProps {
  filters: MonitorFilters;
  onPageChange: (page: number) => void;
  page: number;
}

export function MonitorGeneralTable({ filters, onPageChange, page }: MonitorGeneralTableProps) {
  const tableId = useId();
  const [localPage, setLocalPage] = useState(1);

  const { data, isLoading, isError, refetch } = useMonitorGeneral(filters, localPage);

  const handlePageChange = useCallback(
    (p: number) => {
      setLocalPage(p);
      onPageChange(p);
    },
    [onPageChange],
  );

  const handleExport = () => {
    if (!data?.data?.length) return;
    exportToCsv(data.data, `monitor_general_${Date.now()}.csv`);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={`${tableId}-skeleton-filter-${i}`} className="h-9 w-28 animate-pulse rounded-md bg-neutral-200" />
          ))}
        </div>
        <div className="overflow-x-auto rounded-lg border border-neutral-200">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50">
              <tr>
                {['Alumno', 'Email', 'Comisión', 'Regional', 'Materia', 'Actividad', 'Estado', 'Última actividad'].map(
                  (h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={`${tableId}-row-${i}`} className="animate-pulse border-t border-neutral-100">
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
        <p className="text-danger-600">Error al cargar datos del monitor</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
        <p className="text-neutral-600">No se encontraron resultados</p>
        <p className="mt-1 text-sm text-neutral-500">
          Ajustá los filtros o importá datos para comenzar
        </p>
      </div>
    );
  }

  const from = (data.page - 1) * PER_PAGE + 1;
  const to = Math.min(data.page * PER_PAGE, data.total);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-neutral-500">
          Mostrando {from}–{to} de {data.total}
        </p>
        <button
          onClick={handleExport}
          className="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-50"
        >
          Exportar CSV
        </button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-neutral-200">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50">
            <tr>
              {['Alumno', 'Email', 'Comisión', 'Regional', 'Materia', 'Actividad', 'Estado', 'Última actividad'].map(
                (h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {data.data.map((entry) => (
              <tr key={entry.alumno_id} className="border-t border-neutral-100 hover:bg-neutral-50">
                <td className="px-4 py-3 font-medium text-neutral-900">{entry.nombre}</td>
                <td className="px-4 py-3 text-neutral-700">{entry.email}</td>
                <td className="px-4 py-3 text-neutral-700">{entry.comision}</td>
                <td className="px-4 py-3 text-neutral-700">{entry.regional}</td>
                <td className="px-4 py-3 text-neutral-700">{entry.materia}</td>
                <td className="px-4 py-3 text-neutral-700">{entry.actividad}</td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      entry.estado === 'activo' || entry.estado === 'al_dia'
                        ? 'bg-success-100 text-success-700'
                        : entry.estado === 'atrasado'
                          ? 'bg-danger-100 text-danger-700'
                          : 'bg-neutral-100 text-neutral-600'
                    }`}
                  >
                    {entry.estado}
                  </span>
                </td>
                <td className="px-4 py-3 text-neutral-600">
                  {entry.ultima_actividad
                    ? new Date(entry.ultima_actividad).toLocaleDateString()
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-neutral-500">
            Mostrando {from}–{to} de {data.total}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => handlePageChange(Math.max(1, localPage - 1))}
              disabled={localPage <= 1}
              className="rounded-md border border-neutral-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Anterior
            </button>
            <button
              onClick={() => handlePageChange(Math.min(data.total_pages, localPage + 1))}
              disabled={localPage >= data.total_pages}
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
