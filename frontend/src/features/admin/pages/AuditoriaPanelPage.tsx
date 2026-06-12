import { lazy, Suspense, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { Spinner } from '@/shared/components/ui/Spinner';
import KPICard from '@/shared/components/KPICard';
import {
  useAccionesPorDia,
  useComunicacionesPorDocente,
  useInteraccionesPorDocenteMateria,
  useUltimasAcciones,
} from '../hooks/useAuditoria';
import ChartSkeleton from '../components/auditoria/ChartSkeleton';
import ScopeBadge from '../components/auditoria/ScopeBadge';
import type { UltimaAccion } from '../types/auditoria.types';

const AccionesPorDiaChart = lazy(() => import('../components/auditoria/AccionesPorDiaChart'));
const ComunicacionesChart = lazy(() => import('../components/auditoria/ComunicacionesChart'));
const InteraccionesChart = lazy(() => import('../components/auditoria/InteraccionesChart'));

export default function AuditoriaPanelPage() {
  const navigate = useNavigate();
  const [isPropio] = useState(false); // TODO: derive from auth context / backend response

  const { data: acciones, isLoading: accionesLoading } = useAccionesPorDia();
  const { data: comunicaciones, isLoading: comunicacionesLoading } = useComunicacionesPorDocente();
  const { data: interacciones, isLoading: interaccionesLoading } = useInteraccionesPorDocenteMateria();
  const { data: ultimas, isLoading: ultimasLoading } = useUltimasAcciones();

  const totalAcciones = acciones?.reduce((sum, a) => sum + a.cantidad, 0) ?? 0;
  const totalComunicaciones = comunicaciones?.reduce((sum, c) => sum + c.enviadas + c.pendientes + c.fallidas, 0) ?? 0;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight">Auditoría</h1>
          <ScopeBadge isPropio={isPropio} />
        </div>
        <Button variant="outline" onClick={() => navigate('/admin/auditoria/log')}>
          Ver log completo
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard title="Total acciones" value={totalAcciones} />
        <KPICard title="Total comunicaciones" value={totalComunicaciones} />
        <KPICard title="Docentes activos" value={comunicaciones?.length ?? 0} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Suspense fallback={<ChartSkeleton />}>
          {accionesLoading ? <ChartSkeleton /> : <AccionesPorDiaChart data={acciones ?? []} />}
        </Suspense>
        <Suspense fallback={<ChartSkeleton />}>
          {comunicacionesLoading ? <ChartSkeleton /> : <ComunicacionesChart data={comunicaciones ?? []} />}
        </Suspense>
        <Suspense fallback={<ChartSkeleton />}>
          {interaccionesLoading ? <ChartSkeleton /> : <InteraccionesChart data={interacciones ?? []} />}
        </Suspense>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Últimas acciones</CardTitle>
        </CardHeader>
        <CardContent>
          {ultimasLoading && (
            <div className="flex items-center gap-2 py-4">
              <Spinner size="sm" />
              <span className="text-sm text-muted-foreground">Cargando...</span>
            </div>
          )}
          {ultimas && (
            <div className="space-y-2">
              {ultimas.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-md border border-border p-3">
                  <div className="space-y-1">
                    <div className="text-sm font-medium">
                      {item.accion} — {item.modulo}
                    </div>
                    <div className="text-xs text-muted-foreground">{item.descripcion}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">{item.usuario_nombre}</div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(item.timestamp).toLocaleString('es-AR')}
                    </div>
                  </div>
                </div>
              ))}
              {ultimas.length === 0 && (
                <div className="py-4 text-center text-sm text-muted-foreground">No hay acciones recientes</div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
