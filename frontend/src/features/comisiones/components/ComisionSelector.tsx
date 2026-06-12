import { useNavigate } from 'react-router-dom';
import { useId } from 'react';
import { cn } from '@/lib/utils';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useComisiones } from '../hooks/useComisiones';

export function ComisionSelector() {
  const selectId = useId();
  const navigate = useNavigate();
  const { data: comisiones, isLoading, isError, refetch } = useComisiones();

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const materiaId = e.target.value;
    if (materiaId) {
      navigate(`/comisiones/${materiaId}`);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">Error al cargar las comisiones.</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!comisiones || comisiones.length === 0) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-6 text-center">
        <p className="text-neutral-600">No tenés comisiones asignadas</p>
        <select
          disabled
          className={cn(
            'mt-4 block w-full rounded-md border border-neutral-300 bg-neutral-100 px-3 py-2 text-sm text-neutral-400',
          )}
        >
          <option>Sin comisiones disponibles</option>
        </select>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <label htmlFor={selectId} className="block text-sm font-medium text-neutral-700">
        Seleccioná una comisión para empezar
      </label>
      <select
        id={selectId}
        onChange={handleChange}
        defaultValue=""
        className="block w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
      >
        <option value="" disabled>
          Seleccioná una comisión...
        </option>
        {comisiones.map((c) => (
          <option key={c.materia_id} value={c.materia_id}>
            {c.materia_nombre} — {c.cohorte_nombre}
          </option>
        ))}
      </select>
    </div>
  );
}
