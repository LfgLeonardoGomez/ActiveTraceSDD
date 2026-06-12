import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { Spinner } from '@/shared/components/ui/Spinner';
import SegmentTabs from '@/shared/components/SegmentTabs';
import { useLiquidacion, useCerrarLiquidacion } from '../hooks/useLiquidaciones';
import PeriodoSelector from '../components/liquidaciones/PeriodoSelector';
import KpiCards from '../components/liquidaciones/KpiCards';
import SegmentedTable from '../components/liquidaciones/SegmentedTable';
import CierreDialog from '../components/liquidaciones/CierreDialog';
import TeacherDetail from '../components/liquidaciones/TeacherDetail';
import type { LiquidacionItem } from '../types/liquidaciones.types';

const SEGMENTS = [
  { key: 'general', label: 'General' },
  { key: 'nexo', label: 'NEXO' },
  { key: 'facturantes', label: 'Facturantes' },
];

export default function LiquidacionesPage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<{ cohorteId: string; mes: string } | null>(null);
  const [activeSegment, setActiveSegment] = useState('general');
  const [showCierre, setShowCierre] = useState(false);
  const [detailItem, setDetailItem] = useState<LiquidacionItem | null>(null);

  const { data, isLoading, error } = useLiquidacion(
    selected?.cohorteId ?? '',
    selected?.mes ?? '',
  );

  const cerrar = useCerrarLiquidacion();

  const handlePeriodoChange = (cohorteId: string, mes: string) => {
    setSelected({ cohorteId, mes });
  };

  const handleCerrar = () => {
    if (!selected) return;
    cerrar.mutate(
      { cohorteId: selected.cohorteId, periodo: selected.mes },
      {
        onSuccess: () => setShowCierre(false),
      },
    );
  };

  const segmentData =
    activeSegment === 'general'
      ? data?.segmento_general ?? []
      : activeSegment === 'nexo'
        ? data?.segmento_nexo ?? []
        : data?.segmento_facturantes ?? [];

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Liquidaciones</h1>
        <Button variant="outline" onClick={() => navigate('/finanzas/historial')}>
          Ver historial
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <PeriodoSelector onChange={handlePeriodoChange} />
        </CardContent>
      </Card>

      {isLoading && (
        <div className="flex items-center gap-2 py-8">
          <Spinner />
          <span className="text-muted-foreground">Cargando liquidación...</span>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-danger-200 bg-danger-50 p-4 text-sm text-danger-700">
          Error al cargar la liquidación.
        </div>
      )}

      {data && (
        <>
          <KpiCards totalSinFactura={data.total_sin_factura} totalConFactura={data.total_con_factura} />

          <div className="flex items-center justify-between">
            <SegmentTabs segments={SEGMENTS} active={activeSegment} onChange={setActiveSegment} />
            {data.estado === 'abierto' && (
              <Button variant="destructive" onClick={() => setShowCierre(true)}>
                Cerrar liquidación
              </Button>
            )}
            {data.estado === 'cerrado' && (
              <span className="rounded-full bg-neutral-100 px-3 py-1 text-xs font-medium text-neutral-600">
                Cerrada
              </span>
            )}
          </div>

          <SegmentedTable
            items={segmentData}
            segment={activeSegment}
            onRowClick={setDetailItem}
          />
        </>
      )}

      <CierreDialog
        open={showCierre}
        onClose={() => setShowCierre(false)}
        onConfirm={handleCerrar}
        periodo={selected?.mes ?? ''}
        isLoading={cerrar.isPending}
      />

      <TeacherDetail item={detailItem} onClose={() => setDetailItem(null)} />
    </div>
  );
}
