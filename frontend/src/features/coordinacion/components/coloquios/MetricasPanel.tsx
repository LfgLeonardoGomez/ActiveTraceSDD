import { useId } from 'react';
import { Spinner } from '@/shared/components/ui/Spinner';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Users, ClipboardList, Calendar, BarChart3 } from 'lucide-react';
import { useMetricasColoquios } from '../../hooks/useColoquios';

interface KpiDef {
  label: string;
  key: keyof import('../../types/coloquios.types').MetricasColoquios;
  Icon: typeof Users;
}

const KPIS: KpiDef[] = [
  { label: 'Total alumnos cargados', key: 'total_alumnos_cargados', Icon: Users },
  { label: 'Instancias activas', key: 'instancias_activas', Icon: ClipboardList },
  { label: 'Reservas activas', key: 'reservas_activas', Icon: Calendar },
  { label: 'Notas registradas', key: 'notas_registradas', Icon: BarChart3 },
];

export function MetricasPanel() {
  const panelId = useId();
  const { data: metricas, isLoading, isError, refetch } = useMetricasColoquios();

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={`${panelId}-skeleton-${i}`}
            className="animate-pulse rounded-lg border border-neutral-200 bg-white p-6"
          >
            <div className="mb-3 h-4 w-3/4 rounded bg-neutral-200" />
            <div className="h-8 w-16 rounded bg-neutral-100" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-danger-200 bg-danger-50 p-4">
        <p className="text-sm text-danger-600">Error al cargar métricas</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm font-medium text-primary-600 hover:underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-neutral-900">Métricas de coloquios</h2>
        <button
          onClick={() => refetch()}
          className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-50"
        >
          Actualizar
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {KPIS.map((kpi) => {
          const value = metricas ? metricas[kpi.key] : 0;
          const Icon = kpi.Icon;
          return (
            <Card key={kpi.key}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-neutral-500">
                  {kpi.label}
                </CardTitle>
                <Icon className={`size-5 ${value === 0 ? 'text-neutral-400' : 'text-primary-600'}`} />
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-neutral-900">
                  {value}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
