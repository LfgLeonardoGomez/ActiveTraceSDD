import { useState, useEffect } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Search, X } from 'lucide-react';
import type { MonitorFilters as MonitorFiltersType } from '../types/comisiones.types';

interface MonitorFiltersProps {
  onFiltersChange: (filters: MonitorFiltersType) => void;
  isLoading: boolean;
  showDateRange?: boolean;
}

export function MonitorFilters({
  onFiltersChange,
  isLoading,
  showDateRange = false,
}: MonitorFiltersProps) {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [comision, setComision] = useState('');
  const [regional, setRegional] = useState('');
  const [actividad, setActividad] = useState('');
  const [minActividades, setMinActividades] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [dateError, setDateError] = useState<string | null>(null);

  useEffect(() => {
    if (fechaDesde && fechaHasta && fechaDesde > fechaHasta) {
      setDateError('La fecha desde debe ser anterior a la fecha hasta');
      return;
    }
    setDateError(null);

    const timer = setTimeout(() => {
      onFiltersChange({
        ...(nombre ? { nombre } : {}),
        ...(email ? { email } : {}),
        ...(comision ? { comision } : {}),
        ...(regional ? { regional } : {}),
        ...(actividad ? { actividad } : {}),
        ...(minActividades ? { min_actividades_completadas: Number(minActividades) } : {}),
        ...(fechaDesde ? { fecha_desde: fechaDesde } : {}),
        ...(fechaHasta ? { fecha_hasta: fechaHasta } : {}),
      });
    }, 300);

    return () => clearTimeout(timer);
  }, [nombre, email, comision, regional, actividad, minActividades, fechaDesde, fechaHasta, onFiltersChange]);

  const handleClear = () => {
    setNombre('');
    setEmail('');
    setComision('');
    setRegional('');
    setActividad('');
    setMinActividades('');
    setFechaDesde('');
    setFechaHasta('');
    setDateError(null);
    onFiltersChange({});
  };

  const hasAnyFilter = nombre || email || comision || regional || actividad || minActividades || fechaDesde || fechaHasta;

  return (
    <div className="space-y-3 rounded-lg border border-neutral-200 bg-white p-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
          <input
            type="text"
            placeholder="Alumno"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            disabled={isLoading}
            className="w-full rounded-md border border-neutral-300 py-1.5 pl-8 pr-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:opacity-50"
          />
        </div>
        <input
          type="text"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={isLoading}
          className="w-full rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:opacity-50"
        />
        <input
          type="text"
          placeholder="Comisión"
          value={comision}
          onChange={(e) => setComision(e.target.value)}
          disabled={isLoading}
          className="w-full rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:opacity-50"
        />
        <input
          type="text"
          placeholder="Regional"
          value={regional}
          onChange={(e) => setRegional(e.target.value)}
          disabled={isLoading}
          className="w-full rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:opacity-50"
        />
        <input
          type="text"
          placeholder="Actividad"
          value={actividad}
          onChange={(e) => setActividad(e.target.value)}
          disabled={isLoading}
          className="w-full rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:opacity-50"
        />
        <input
          type="number"
          placeholder="Min. actividades completadas"
          value={minActividades}
          onChange={(e) => setMinActividades(e.target.value)}
          disabled={isLoading}
          min={0}
          className="w-full rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:opacity-50"
        />
        {showDateRange && (
          <>
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Fecha desde</label>
              <input
                type="date"
                value={fechaDesde}
                onChange={(e) => setFechaDesde(e.target.value)}
                disabled={isLoading}
                className="w-full rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Fecha hasta</label>
              <input
                type="date"
                value={fechaHasta}
                onChange={(e) => setFechaHasta(e.target.value)}
                disabled={isLoading}
                className="w-full rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
          </>
        )}
      </div>

      {dateError && (
        <div className="rounded-md bg-danger-50 p-2 text-xs text-danger-600">{dateError}</div>
      )}

      {hasAnyFilter && (
        <div className="flex justify-end">
          <Button variant="ghost" size="sm" onClick={handleClear}>
            <X className="mr-1 h-4 w-4" />
            Limpiar filtros
          </Button>
        </div>
      )}
    </div>
  );
}
