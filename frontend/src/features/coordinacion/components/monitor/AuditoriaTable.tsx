import { useState, useId } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useDebounce } from '@/shared/hooks/useDebounce';
import { useAuditoria } from '../../hooks/useMonitorCoordinacion';
import { MonitorFilters } from './MonitorFilters';
import type { MonitorFilters as Filters, AuditoriaEntry } from '../../types/monitor.types';

const PER_PAGE = 50;

function csvEscape(val: string | null | undefined): string {
  if (val == null) return '';
  const s = String(val);
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function exportToCsv(rows: AuditoriaEntry[], filename: string) {
  const headers = ['Fecha/Hora', 'Docente', 'Rol', 'Acción', 'Materia', 'Registros afectados', 'IP', 'User-Agent'];
  const lines = rows.map((r) =>
    [r.fecha_hora, r.docente, r.rol, r.accion, r.materia, String(r.registros_afectados), r.ip, r.user_agent]
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

function DetailRow({ entry }: { entry: AuditoriaEntry }) {
  return (
    <tr className="bg-neutral-50">
      <td colSpan={9} className="px-4 py-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-neutral-700">Request payload:</span>
            <pre className="mt-1 max-h-32 overflow-auto rounded bg-white p-2 text-xs text-neutral-600">
              {entry.detalle.request_payload ?? '—'}
            </pre>
          </div>
          <div>
            <span className="font-medium text-neutral-700">Response status:</span>
            <span className="ml-2 text-neutral-600">{entry.detalle.response_status ?? '—'}</span>
          </div>
          <div>
            <span className="font-medium text-neutral-700">Duración:</span>
            <span className="ml-2 text-neutral-600">
              {entry.detalle.duration != null ? `${entry.detalle.duration}ms` : '—'}
            </span>
          </div>
          <div>
            <span className="font-medium text-neutral-700">User-Agent completo:</span>
            <p className="mt-1 max-h-16 overflow-auto break-all rounded bg-white p-2 text-xs text-neutral-600">
              {entry.detalle.full_user_agent ?? '—'}
            </p>
          </div>
        </div>
      </td>
    </tr>
  );
}

export function AuditoriaTable() {
  const tableId = useId();
  const [filters, setFilters] = useState<Filters>({});
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [isLoadingFilters, setIsLoadingFilters] = useState(false);

  const { data, isLoading, isError, refetch } = useAuditoria(filters, page);

  const handleFiltersChange = (newFilters: Filters) => {
    setFilters(newFilters);
    setPage(1);
    setExpanded(new Set());
  };

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleExport = () => {
    if (!data?.data?.length) return;
    exportToCsv(data.data, `auditoria_${Date.now()}.csv`);
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
                <th className="w-8 px-4 py-3" />
                {['Fecha/Hora', 'Docente', 'Rol', 'Acción', 'Materia', 'Registros afectados', 'IP', 'User-Agent'].map(
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
                  {Array.from({ length: 9 }).map((_, j) => (
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
        <p className="text-danger-600">Error al cargar auditoría</p>
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
        <p className="text-neutral-600">No se encontraron registros de auditoría</p>
        <p className="mt-1 text-sm text-neutral-500">
          Ajustá los filtros para ver resultados
        </p>
      </div>
    );
  }

  const from = (data.page - 1) * PER_PAGE + 1;
  const to = Math.min(data.page * PER_PAGE, data.total);

  return (
    <div className="space-y-4">
      <MonitorFilters
        mode="auditoria"
        isLoading={isLoadingFilters}
        onFiltersChange={handleFiltersChange}
      />

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
              <th className="w-8 px-4 py-3" />
              {['Fecha/Hora', 'Docente', 'Rol', 'Acción', 'Materia', 'Registros afectados', 'IP', 'User-Agent'].map(
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
              <>
                <tr
                  key={entry.id}
                  className="cursor-pointer border-t border-neutral-100 hover:bg-neutral-50"
                  onClick={() => toggleExpand(entry.id)}
                >
                  <td className="px-4 py-3">
                    {expanded.has(entry.id) ? (
                      <ChevronDown className="size-4 text-neutral-400" />
                    ) : (
                      <ChevronRight className="size-4 text-neutral-400" />
                    )}
                  </td>
                  <td className="px-4 py-3 text-neutral-900">
                    {new Date(entry.fecha_hora).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-medium text-neutral-900">{entry.docente}</td>
                  <td className="px-4 py-3 text-neutral-700">{entry.rol}</td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                      {entry.accion}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-neutral-700">{entry.materia ?? '—'}</td>
                  <td className="px-4 py-3 text-neutral-700">{entry.registros_afectados}</td>
                  <td className="px-4 py-3 font-mono text-xs text-neutral-600">{entry.ip}</td>
                  <td className="max-w-[200px] truncate px-4 py-3 text-xs text-neutral-600" title={entry.user_agent}>
                    {entry.user_agent}
                  </td>
                </tr>
                {expanded.has(entry.id) && <DetailRow key={`${entry.id}-detail`} entry={entry} />}
              </>
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
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded-md border border-neutral-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Anterior
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
              disabled={page >= data.total_pages}
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
