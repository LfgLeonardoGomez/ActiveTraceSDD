import { useState, useId } from 'react';
import { useTareasAdmin, useActualizarEstadoTarea } from '../../hooks/useTareas';
import { TareaStatusBadge } from './TareaStatusBadge';
import { TareaCommentThread } from './TareaCommentThread';
import type { TareaEstado, TareaFilters } from '../../types/tareas.types';

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString();
}

function getPriorityColor(p: string): string {
  switch (p) {
    case 'urgente': return 'text-red-600 font-semibold';
    case 'alta': return 'text-orange-600';
    case 'baja': return 'text-neutral-400';
    default: return 'text-neutral-600';
  }
}

export function TareaTable() {
  const tableId = useId();
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState<TareaFilters>({});
  const [actionDropdown, setActionDropdown] = useState<string | null>(null);
  const [rejectComment, setRejectComment] = useState<Record<string, string>>({});
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const perPage = 25;

  const { data: tareas, isLoading, isError, refetch } = useTareasAdmin(filters);
  const actualizarEstado = useActualizarEstadoTarea();

  const handleFilterChange = (key: keyof TareaFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
    setPage(0);
  };

  const handleAction = (id: string, estado: TareaEstado, comment?: string) => {
    if (estado === 'rechazada' && !comment) return;
    actualizarEstado.mutate({ id, estado, comentario: comment });
    setActionDropdown(null);
    setRejectingId(null);
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
                {['Título', 'Asignado a', 'Asignador', 'Materia', 'Estado', 'Prioridad', 'Fecha límite', 'Creada', 'Acciones'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={`${tableId}-row-skeleton-${i}`} className="animate-pulse border-t border-neutral-100">
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
        <p className="text-danger-600">Error al cargar tareas</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!tareas || tareas.length === 0) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
        <p className="text-neutral-600">No hay tareas registradas en el sistema</p>
      </div>
    );
  }

  const paginated = tareas.slice(page * perPage, (page + 1) * perPage);
  const totalPages = Math.ceil(tareas.length / perPage);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <input
          placeholder="Buscar título..."
          className="h-9 rounded-md border border-neutral-300 px-3 text-sm"
          onChange={(e) => handleFilterChange('q', e.target.value)}
        />
        <input
          placeholder="Docente..."
          className="h-9 rounded-md border border-neutral-300 px-3 text-sm"
          onChange={(e) => handleFilterChange('docente', e.target.value)}
        />
        <input
          placeholder="Asignador..."
          className="h-9 rounded-md border border-neutral-300 px-3 text-sm"
          onChange={(e) => handleFilterChange('asignador', e.target.value)}
        />
        <input
          placeholder="Materia..."
          className="h-9 rounded-md border border-neutral-300 px-3 text-sm"
          onChange={(e) => handleFilterChange('materia', e.target.value)}
        />
        <select
          className="h-9 rounded-md border border-neutral-300 px-3 text-sm"
          onChange={(e) => handleFilterChange('estado', e.target.value)}
          value={filters.estado || ''}
        >
          <option value="">Todos los estados</option>
          <option value="pendiente">Pendiente</option>
          <option value="en_proceso">En proceso</option>
          <option value="completada">Completada</option>
          <option value="aprobada">Aprobada</option>
          <option value="rechazada">Rechazada</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded-lg border border-neutral-200">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50">
            <tr>
              {['Título', 'Asignado a', 'Asignador', 'Materia', 'Estado', 'Prioridad', 'Fecha límite', 'Creada', 'Acciones'].map((h) => (
                <th key={h} className="px-4 py-3 text-left font-medium text-neutral-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginated.map((t) => (
              <tr key={t.id} className="border-t border-neutral-100 hover:bg-neutral-50">
                <td className="px-4 py-3 font-medium text-neutral-900">{t.titulo}</td>
                <td className="px-4 py-3 text-neutral-700">{t.asignado}</td>
                <td className="px-4 py-3 text-neutral-700">{t.asignador}</td>
                <td className="px-4 py-3 text-neutral-700">{t.materia || '—'}</td>
                <td className="px-4 py-3">
                  <TareaStatusBadge estado={t.estado} />
                </td>
                <td className={`px-4 py-3 ${getPriorityColor(t.prioridad)}`}>
                  {t.prioridad ? t.prioridad.charAt(0).toUpperCase() + t.prioridad.slice(1) : 'Normal'}
                </td>
                <td className="px-4 py-3 text-neutral-600">
                  {t.fecha_limite ? formatDate(t.fecha_limite) : '—'}
                </td>
                <td className="px-4 py-3 text-neutral-600">{formatDate(t.fecha_creacion)}</td>
                <td className="px-4 py-3 relative">
                  {['completada'].includes(t.estado) && (
                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => setActionDropdown(actionDropdown === t.id ? null : t.id)}
                        className="rounded-md border border-neutral-300 px-2 py-1 text-xs font-medium text-neutral-600 hover:bg-neutral-100"
                      >
                        Acciones
                      </button>

                      {actionDropdown === t.id && (
                        <div className="absolute right-0 top-full z-10 mt-1 w-40 rounded-md border border-neutral-200 bg-white shadow-lg">
                          <button
                            type="button"
                            onClick={() => handleAction(t.id, 'aprobada')}
                            className="flex w-full items-center px-3 py-2 text-left text-xs font-medium text-emerald-700 hover:bg-neutral-50"
                          >
                            Aprobar
                          </button>
                          <button
                            type="button"
                            onClick={() => setRejectingId(t.id)}
                            className="flex w-full items-center px-3 py-2 text-left text-xs font-medium text-red-700 hover:bg-neutral-50"
                          >
                            Rechazar
                          </button>
                        </div>
                      )}

                      {rejectingId === t.id && (
                        <div className="absolute right-0 top-full z-20 mt-1 w-64 rounded-md border border-neutral-200 bg-white p-3 shadow-lg">
                          <p className="mb-2 text-xs font-medium text-neutral-700">Motivo del rechazo</p>
                          <textarea
                            value={rejectComment[t.id] || ''}
                            onChange={(e) => setRejectComment((prev) => ({ ...prev, [t.id]: e.target.value }))}
                            rows={2}
                            placeholder="Escribí el motivo..."
                            className="w-full rounded-md border border-neutral-300 px-2 py-1 text-xs placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none"
                          />
                          <div className="mt-2 flex gap-2">
                            <button
                              type="button"
                              onClick={() => { setRejectingId(null); setRejectComment((prev) => ({ ...prev, [t.id]: '' })); }}
                              className="rounded-md border border-neutral-300 px-2 py-1 text-xs text-neutral-600 hover:bg-neutral-50"
                            >
                              Cancelar
                            </button>
                            <button
                              type="button"
                              onClick={() => handleAction(t.id, 'rechazada', rejectComment[t.id])}
                              disabled={!rejectComment[t.id]?.trim()}
                              className="rounded-md bg-red-600 px-2 py-1 text-xs text-white hover:bg-red-700 disabled:opacity-50"
                            >
                              Rechazar
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-neutral-500">
            Mostrando {page * perPage + 1}–{Math.min((page + 1) * perPage, tareas.length)} de {tareas.length}
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
