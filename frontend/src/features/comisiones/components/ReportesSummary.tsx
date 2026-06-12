import { useReporteRapido } from '../hooks/useReporteRapido';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { AlertTriangle } from 'lucide-react';

interface ReportesSummaryProps {
  materiaId: string;
}

export function ReportesSummary({ materiaId }: ReportesSummaryProps) {
  const { data, isLoading, isError, refetch } = useReporteRapido(materiaId);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="h-4 w-24 animate-pulse rounded bg-neutral-200" />
              <div className="mt-2 h-8 w-16 animate-pulse rounded bg-neutral-200" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center">
        <p className="text-danger-600">Error al cargar los reportes</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!data || (data.total_alumnos === 0 && data.aprobados === 0)) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p className="text-neutral-600">
            No hay datos de esta comisión. Importá calificaciones para ver reportes.
          </p>
        </CardContent>
      </Card>
    );
  }

  const pct =
    data.total_alumnos > 0
      ? Math.round((data.aprobados / data.total_alumnos) * 100)
      : 0;

  const pctColor =
    pct >= 70 ? 'text-success-600' : pct >= 40 ? 'text-warning-600' : 'text-danger-600';

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-600">Total alumnos</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold">{data.total_alumnos}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-600">
            Con al menos una aprobada
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-success-600">{data.aprobados}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-600">Atrasados</CardTitle>
        </CardHeader>
        <CardContent>
          <p className={`text-3xl font-bold ${data.pendientes > 0 ? 'text-warning-600' : ''}`}>
            {data.pendientes}
          </p>
          {data.pendientes > 0 && <AlertTriangle className="mt-1 h-4 w-4 text-warning-500" />}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-600">
            Porcentaje de aprobación
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className={`text-3xl font-bold ${pctColor}`}>{pct}%</p>
        </CardContent>
      </Card>
    </div>
  );
}
