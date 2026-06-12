import { useTpsSinCorregir, getTpsSinCorregirExportUrl } from '../hooks/useTpsSinCorregir';
import { ExportButton } from './ExportButton';

interface TpsSinCorregirTableProps {
  materiaId: string;
}

export function TpsSinCorregirTable({ materiaId }: TpsSinCorregirTableProps) {
  const { data, isLoading, isError, refetch } = useTpsSinCorregir(materiaId);

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
        <p>Error al cargar los trabajos sin corregir</p>
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
      <div className="space-y-4">
        <div className="rounded-lg border border-neutral-200 p-8 text-center">
          <p className="text-sm text-neutral-600">
            No hay trabajos prácticos sin corregir
          </p>
        </div>
        <ExportButton
          exportUrl={getTpsSinCorregirExportUrl(materiaId)}
          disabled
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-neutral-700">
          Se detectaron {data.length} entregas sin corregir
        </p>
        <ExportButton exportUrl={getTpsSinCorregirExportUrl(materiaId)} />
      </div>

      <div className="overflow-x-auto rounded-md border border-neutral-200">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Alumno
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Email
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Actividad
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Fecha de entrega
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {data.map((entry, i) => (
              <tr key={i} className="hover:bg-neutral-50">
                <td className="px-3 py-2 font-medium text-neutral-900">{entry.nombre}</td>
                <td className="px-3 py-2 text-neutral-600">{entry.email || '—'}</td>
                <td className="px-3 py-2">{entry.actividad}</td>
                <td className="px-3 py-2 text-neutral-600">{entry.fecha_entrega}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
