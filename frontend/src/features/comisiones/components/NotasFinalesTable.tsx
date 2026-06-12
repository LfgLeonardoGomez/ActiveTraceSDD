import { useNotasFinales, getNotasFinalesExportUrl } from '../hooks/useNotasFinales';
import { Button } from '@/shared/components/ui/Button';
import { Download } from 'lucide-react';

interface NotasFinalesTableProps {
  materiaId: string;
}

export function NotasFinalesTable({ materiaId }: NotasFinalesTableProps) {
  const { data, isLoading, isError, refetch } = useNotasFinales(materiaId);

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
        <p>Error al cargar las notas finales</p>
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
            No hay notas finales para mostrar. Importá calificaciones primero.
          </p>
        </div>
        <Button variant="outline" size="sm" disabled>
          <Download className="mr-2 h-4 w-4" />
          Exportar CSV
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            window.open(getNotasFinalesExportUrl(materiaId), '_blank');
          }}
        >
          <Download className="mr-2 h-4 w-4" />
          Exportar CSV
        </Button>
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
                Nota final
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                Estado
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {data.map((entry) => (
              <tr key={entry.alumno_id} className="hover:bg-neutral-50">
                <td className="px-3 py-2 font-medium text-neutral-900">{entry.nombre}</td>
                <td className="px-3 py-2 text-neutral-600">{entry.email}</td>
                <td className="px-3 py-2">
                  {entry.nota_final != null ? entry.nota_final.toFixed(2) : '—'}
                </td>
                <td className="px-3 py-2">
                  <span
                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                      entry.estado === 'aprobado' || entry.estado === 'promociona'
                        ? 'bg-success-50 text-success-700'
                        : entry.estado === 'libre'
                          ? 'bg-danger-50 text-danger-700'
                          : 'bg-warning-50 text-warning-700'
                    }`}
                  >
                    {entry.estado === 'aprobado'
                      ? 'Aprobado'
                      : entry.estado === 'promociona'
                        ? 'Promociona'
                        : entry.estado === 'libre'
                          ? 'Libre'
                          : entry.estado === 'desaprobado'
                            ? 'Desaprobado'
                            : 'Pendiente'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
