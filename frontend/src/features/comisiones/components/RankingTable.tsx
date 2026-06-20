import { useRanking } from '../hooks/useRanking';
import { Button } from '@/shared/components/ui/Button';
import { Trophy, Medal, Award } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface RankingTableProps {
  materiaId: string;
}

export function RankingTable({ materiaId }: RankingTableProps) {
  const { data, isLoading, isError, refetch } = useRanking(materiaId);
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex gap-3">
            <div className="h-10 w-10 animate-pulse rounded bg-neutral-200" />
            <div className="h-10 flex-1 animate-pulse rounded bg-neutral-200" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-md bg-danger-50 p-4 text-sm text-danger-600">
        <p>Error al cargar el ranking</p>
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
      <div className="rounded-lg border border-neutral-200 p-8 text-center">
        <Trophy className="mx-auto h-10 w-10 text-neutral-300" />
        <p className="mt-3 text-sm font-medium text-neutral-600">
          No hay actividades importadas para mostrar ranking
        </p>
        <Button
          variant="link"
          size="sm"
          className="mt-2"
          onClick={() => navigate(`/comisiones/${materiaId}/importar`)}
        >
          Importar calificaciones
        </Button>
      </div>
    );
  }

  const getPositionIcon = (pos: number) => {
    if (pos === 1) return <Trophy className="h-5 w-5 text-yellow-500" />;
    if (pos === 2) return <Medal className="h-5 w-5 text-neutral-400" />;
    if (pos === 3) return <Award className="h-5 w-5 text-amber-700" />;
    return null;
  };

  const getRowClass = (pos: number) => {
    if (pos === 1) return 'bg-yellow-50';
    if (pos === 2) return 'bg-neutral-50';
    if (pos === 3) return 'bg-amber-50';
    return '';
  };

  return (
    <div className="overflow-x-auto rounded-md border border-neutral-200">
      <table className="w-full text-sm">
        <thead className="bg-neutral-50">
          <tr>
            <th className="w-14 px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
              #
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
              Alumno
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
              Email
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
              Act. aprobadas
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
              Total act.
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
              Porcentaje
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-200">
          {data.map((entry) => {
            const pos = entry.posicion;

            return (
              <tr key={entry.entrada_padron_id} className={`${getRowClass(pos)} hover:bg-neutral-100`}>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-1.5">
                    {getPositionIcon(pos)}
                    <span className="font-medium text-neutral-700">{pos}</span>
                  </div>
                </td>
                <td className="px-3 py-2 font-medium text-neutral-900">{entry.alumno_nombre}</td>
                <td className="px-3 py-2 text-neutral-600">—</td>
                <td className="px-3 py-2">{entry.actividades_aprobadas}</td>
                <td className="px-3 py-2">—</td>
                <td className="px-3 py-2">—</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
