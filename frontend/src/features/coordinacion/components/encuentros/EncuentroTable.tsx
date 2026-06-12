import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input } from '@/shared/components/ui/Input';
import { Button } from '@/shared/components/ui/Button';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useEncuentros } from '../../hooks/useEncuentros';
import type { EncuentroFilters } from '../../types/encuentros.types';

const ESTADOS = [
  { value: 'programado', label: 'Programado' },
  { value: 'realizado', label: 'Realizado' },
  { value: 'cancelado', label: 'Cancelado' },
] as const;

export function EncuentroTable() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<EncuentroFilters>({});
  const [page, setPage] = useState(1);
  const { data: encuentros, isLoading, isError, refetch } = useEncuentros({ ...filters, page: String(page), per_page: '50' });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-neutral-900">Encuentros</h2>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => navigate('/coordinacion/encuentros/nuevo')}
          >
            + Nuevo encuentro
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate('/coordinacion/encuentros/recurrente')}
          >
            + Serie recurrente
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <Input
          placeholder="Materia..."
          className="w-48"
          value={filters.materia_id ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, materia_id: e.target.value || undefined })); setPage(1); }}
        />
        <Input
          placeholder="Docente..."
          className="w-48"
          value={filters.docente_id ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, docente_id: e.target.value || undefined })); setPage(1); }}
        />
        <select
          className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
          value={filters.estado ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, estado: e.target.value || undefined })); setPage(1); }}
        >
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e.value} value={e.value}>{e.label}</option>
          ))}
        </select>
        <Input
          type="date"
          className="w-44"
          value={filters.fecha_desde ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, fecha_desde: e.target.value || undefined })); setPage(1); }}
        />
        <Input
          type="date"
          className="w-44"
          value={filters.fecha_hasta ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, fecha_hasta: e.target.value || undefined })); setPage(1); }}
        />
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 animate-pulse rounded-md bg-neutral-100" />
          ))}
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
          <p className="text-danger-600">Error al cargar encuentros</p>
          <button onClick={() => refetch()} className="mt-2 text-sm font-medium text-primary-600 hover:underline">
            Reintentar
          </button>
        </div>
      ) : !encuentros || encuentros.length === 0 ? (
        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
          <p className="text-neutral-600">No hay encuentros programados</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 text-left">
                <th className="pb-3 pr-4 font-medium text-neutral-600">Materia</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Cohorte</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Docente</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Fecha</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Hora</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Título</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Estado</th>
                <th className="pb-3 pr-4 font-medium text-neutral-600">Enlace</th>
                <th className="pb-3 font-medium text-neutral-600">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {encuentros.map((enc) => (
                <tr key={enc.id} className="border-b border-neutral-100 hover:bg-neutral-50">
                  <td className="py-3 pr-4 text-neutral-900">{enc.materia}</td>
                  <td className="py-3 pr-4 text-neutral-600">{enc.cohorte}</td>
                  <td className="py-3 pr-4 text-neutral-900">{enc.docente}</td>
                  <td className="py-3 pr-4 text-neutral-600">{new Date(enc.fecha).toLocaleDateString()}</td>
                  <td className="py-3 pr-4 text-neutral-600">{enc.hora}</td>
                  <td className="py-3 pr-4 text-neutral-900">{enc.titulo ?? '—'}</td>
                  <td className="py-3 pr-4">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        enc.estado === 'programado' ? 'bg-blue-100 text-blue-700' :
                        enc.estado === 'realizado' ? 'bg-green-100 text-green-700' :
                        'bg-red-100 text-red-700'
                      }`}
                    >
                      {enc.estado === 'programado' ? 'Programado' :
                       enc.estado === 'realizado' ? 'Realizado' : 'Cancelado'}
                    </span>
                  </td>
                  <td className="py-3 pr-4">
                    {enc.enlace ? (
                      <a href={enc.enlace} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                        Abrir
                      </a>
                    ) : '—'}
                  </td>
                  <td className="py-3">
                    <button
                      onClick={() => navigate(`/coordinacion/encuentros/${enc.id}/editar`)}
                      className="text-sm font-medium text-primary-600 hover:underline"
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
