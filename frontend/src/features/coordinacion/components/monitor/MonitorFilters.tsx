import { useState, useCallback } from 'react';
import { useDebounce } from '@/shared/hooks/useDebounce';
import type { MonitorFilters as Filters } from '../../types/monitor.types';

interface MonitorFiltersProps {
  mode: 'general' | 'auditoria';
  isLoading: boolean;
  onFiltersChange: (filters: Filters) => void;
}

const INITIAL_FILTERS: Filters = {};

export function MonitorFilters({ mode, isLoading, onFiltersChange }: MonitorFiltersProps) {
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
  const [dateError, setDateError] = useState<string | null>(null);

  const debouncedFilters = useDebounce(filters, 300);

  const notifyParent = useCallback(
    (f: Filters) => {
      if (f.fecha_desde && f.fecha_hasta && f.fecha_desde >= f.fecha_hasta) {
        setDateError('fecha_desde debe ser anterior a fecha_hasta');
        return;
      }
      setDateError(null);
      onFiltersChange(f);
    },
    [onFiltersChange],
  );

  const update = (key: keyof Filters, value: string) => {
    const next = { ...filters, [key]: value || undefined };
    setFilters(next);
    notifyParent(next);
  };

  const handleClear = () => {
    setFilters(INITIAL_FILTERS);
    setDateError(null);
    notifyParent(INITIAL_FILTERS);
  };

  const hasAnyFilter = Object.values(filters).some((v) => v !== undefined);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-end gap-3">
        {mode === 'general' && (
          <>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-neutral-500">Nombre</label>
              <input
                placeholder="Nombre..."
                value={filters.nombre ?? ''}
                onChange={(e) => update('nombre', e.target.value)}
                disabled={isLoading}
                className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-neutral-500">Email</label>
              <input
                placeholder="Email..."
                value={filters.email ?? ''}
                onChange={(e) => update('email', e.target.value)}
                disabled={isLoading}
                className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-neutral-500">Comisión</label>
              <input
                placeholder="Comisión..."
                value={filters.comision ?? ''}
                onChange={(e) => update('comision', e.target.value)}
                disabled={isLoading}
                className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-neutral-500">Regional</label>
              <input
                placeholder="Regional..."
                value={filters.regional ?? ''}
                onChange={(e) => update('regional', e.target.value)}
                disabled={isLoading}
                className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-neutral-500">Materia</label>
              <input
                placeholder="Materia..."
                value={filters.materia ?? ''}
                onChange={(e) => update('materia', e.target.value)}
                disabled={isLoading}
                className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-neutral-500">Actividad</label>
              <input
                placeholder="Actividad..."
                value={filters.actividad ?? ''}
                onChange={(e) => update('actividad', e.target.value)}
                disabled={isLoading}
                className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
              />
            </div>
          </>
        )}

        {mode === 'auditoria' && (
          <>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-neutral-500">Docente</label>
              <input
                placeholder="Docente..."
                value={filters.docente ?? ''}
                onChange={(e) => update('docente', e.target.value)}
                disabled={isLoading}
                className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-neutral-500">Materia</label>
              <input
                placeholder="Materia..."
                value={filters.materia ?? ''}
                onChange={(e) => update('materia', e.target.value)}
                disabled={isLoading}
                className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-neutral-500">Tipo de acción</label>
              <input
                placeholder="Ej: login, importar..."
                value={filters.tipo_accion ?? ''}
                onChange={(e) => update('tipo_accion', e.target.value)}
                disabled={isLoading}
                className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
              />
            </div>
          </>
        )}

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-neutral-500">Fecha desde</label>
          <input
            type="date"
            value={filters.fecha_desde ?? ''}
            onChange={(e) => update('fecha_desde', e.target.value)}
            disabled={isLoading}
            className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-neutral-500">Fecha hasta</label>
          <input
            type="date"
            value={filters.fecha_hasta ?? ''}
            onChange={(e) => update('fecha_hasta', e.target.value)}
            disabled={isLoading}
            className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-neutral-500">Búsqueda libre</label>
          <input
            placeholder="Buscar..."
            value={filters.q ?? ''}
            onChange={(e) => update('q', e.target.value)}
            disabled={isLoading}
            className="h-9 w-40 rounded-md border border-neutral-300 bg-white px-3 text-sm disabled:opacity-50"
          />
        </div>

        {hasAnyFilter && (
          <button
            onClick={handleClear}
            disabled={isLoading}
            className="h-9 rounded-md border border-neutral-300 bg-white px-3 text-sm font-medium text-neutral-600 hover:bg-neutral-50 disabled:opacity-50"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      {dateError && (
        <p className="text-sm text-danger-600" role="alert">
          {dateError}
        </p>
      )}
    </div>
  );
}
