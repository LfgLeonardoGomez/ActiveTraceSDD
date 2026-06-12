import { useState, useMemo, useCallback } from 'react';
import { useAtrasados } from '../hooks/useAtrasados';
import { Button } from '@/shared/components/ui/Button';
import { Search, ChevronUp, ChevronDown, AlertTriangle } from 'lucide-react';

interface AtrasadosTableProps {
  materiaId: string;
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
  onCommunicate: () => void;
}

type SortableKey = 'nombre' | 'email' | 'actividades_faltantes' | 'nota_promedio' | 'estado';

export function AtrasadosTable({
  materiaId,
  selectedIds,
  onSelectionChange,
  onCommunicate,
}: AtrasadosTableProps) {
  const { data, isLoading, isError, refetch } = useAtrasados(materiaId);
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortableKey | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const handleSort = useCallback(
    (key: SortableKey) => {
      if (sortKey === key) {
        setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
      } else {
        setSortKey(key);
        setSortDir('asc');
      }
    },
    [sortKey],
  );

  const filtered = useMemo(() => {
    if (!data) return [];
    const sorted = [...data].sort((a, b) => {
      if (!sortKey) return 0;
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    if (!search) return sorted;
    return sorted.filter((s) => s.nombre.toLowerCase().includes(search.toLowerCase()));
  }, [data, sortKey, sortDir, search]);

  const toggleAll = useCallback(() => {
    if (selectedIds.length === filtered.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(filtered.map((s) => s.alumno_id));
    }
  }, [filtered, selectedIds.length, onSelectionChange]);

  const toggleOne = useCallback(
    (id: string) => {
      const next = selectedIds.includes(id)
        ? selectedIds.filter((x) => x !== id)
        : [...selectedIds, id];
      onSelectionChange(next);
    },
    [selectedIds, onSelectionChange],
  );

  const SortIcon = ({ column }: { column: SortableKey }) => {
    if (sortKey !== column) return null;
    return sortDir === 'asc' ? (
      <ChevronUp className="ml-1 inline h-3 w-3" />
    ) : (
      <ChevronDown className="ml-1 inline h-3 w-3" />
    );
  };

  const Th = ({ column, children }: { column: SortableKey; children: React.ReactNode }) => (
    <th
      className="cursor-pointer px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500 hover:text-neutral-700"
      onClick={() => handleSort(column)}
    >
      {children}
      <SortIcon column={column} />
    </th>
  );

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
        <p>Error al cargar los alumnos atrasados</p>
        <button
          onClick={() => refetch()}
          className="mt-2 font-medium text-danger-700 underline hover:text-danger-800"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg border border-success-200 bg-success-50 p-8 text-center">
        <AlertTriangle className="mx-auto h-8 w-8 text-success-500" />
        <p className="mt-2 text-sm font-medium text-success-700">
          No hay alumnos atrasados en esta comisión
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-neutral-700">
          Se detectaron {data.length} alumnos atrasados
          {search && filtered.length !== data.length && (
            <span className="text-neutral-500">
              {' '}
              ({filtered.length} coincidencias)
            </span>
          )}
        </p>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
          <input
            type="text"
            placeholder="Buscar por nombre..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-56 rounded-md border border-neutral-300 py-1.5 pl-8 pr-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>
      </div>

      <div className="overflow-x-auto rounded-md border border-neutral-200">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50">
            <tr>
              <th className="w-10 px-3 py-2">
                <input
                  type="checkbox"
                  checked={filtered.length > 0 && selectedIds.length === filtered.length}
                  onChange={toggleAll}
                  className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                />
              </th>
              <Th column="nombre">Alumno</Th>
              <Th column="email">Email</Th>
              <Th column="actividades_faltantes">Act. faltantes</Th>
              <Th column="nota_promedio">Nota promedio</Th>
              <Th column="estado">Estado</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {filtered.map((alumno) => (
              <tr
                key={alumno.alumno_id}
                className={`hover:bg-neutral-50 ${
                  selectedIds.includes(alumno.alumno_id) ? 'bg-primary-50' : ''
                }`}
              >
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(alumno.alumno_id)}
                    onChange={() => toggleOne(alumno.alumno_id)}
                    className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                  />
                </td>
                <td className="px-3 py-2 font-medium text-neutral-900">{alumno.nombre}</td>
                <td className="px-3 py-2 text-neutral-600">{alumno.email}</td>
                <td className="px-3 py-2">{alumno.actividades_faltantes}</td>
                <td className="px-3 py-2">
                  {alumno.nota_promedio != null ? alumno.nota_promedio.toFixed(2) : '—'}
                </td>
                <td className="px-3 py-2">
                  <span
                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                      alumno.estado === 'promociona'
                        ? 'bg-success-50 text-success-700'
                        : alumno.estado === 'libre'
                          ? 'bg-danger-50 text-danger-700'
                          : 'bg-warning-50 text-warning-700'
                    }`}
                  >
                    {alumno.estado}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedIds.length > 0 && (
        <div className="sticky bottom-4 flex items-center justify-between rounded-lg border border-primary-200 bg-primary-50 p-4 shadow-sm">
          <p className="text-sm font-medium text-primary-800">
            {selectedIds.length} alumno{selectedIds.length !== 1 ? 's' : ''} seleccionado
            {selectedIds.length !== 1 ? 's' : ''}
          </p>
          <Button size="sm" onClick={onCommunicate}>
            Comunicar seleccionados ({selectedIds.length})
          </Button>
        </div>
      )}

      {search && filtered.length === 0 && (
        <p className="py-4 text-center text-sm text-neutral-500">
          No hay resultados para &quot;{search}&quot;
        </p>
      )}
    </div>
  );
}
