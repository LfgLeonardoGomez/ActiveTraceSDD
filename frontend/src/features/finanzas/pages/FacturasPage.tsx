import { useState } from 'react';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useFacturas, useAbonarFactura } from '../hooks/useFacturas';
import FacturaTable from '../components/facturas/FacturaTable';
import FacturaDetail from '../components/facturas/FacturaDetail';
import AbonarButton from '../components/facturas/AbonarButton';
import type { Factura, FacturaFilters } from '../types/facturas.types';

export default function FacturasPage() {
  const [filters, setFilters] = useState<FacturaFilters>({ page: 1, page_size: 50 });
  const [detailItem, setDetailItem] = useState<Factura | null>(null);
  const { data, isLoading } = useFacturas(filters);
  const abonar = useAbonarFactura();

  const handleFilterChange = (key: keyof FacturaFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined, page: 1 }));
  };

  const handleAbonar = (factura: Factura) => {
    abonar.mutate(factura.id);
  };

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold tracking-tight">Facturas</h1>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-3">
            <Input
              label="Docente"
              placeholder="Buscar docente..."
              value={filters.docente_id ?? ''}
              onChange={(e) => handleFilterChange('docente_id', e.target.value)}
              className="w-64"
            />
            <Input
              label="Período"
              placeholder="YYYY-MM"
              value={filters.periodo ?? ''}
              onChange={(e) => handleFilterChange('periodo', e.target.value)}
              className="w-40"
            />
            <div className="space-y-2">
              <label className="text-sm font-medium">Estado</label>
              <select
                value={filters.estado ?? ''}
                onChange={(e) => handleFilterChange('estado', e.target.value)}
                className="h-10 w-40 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
              >
                <option value="">Todos</option>
                <option value="pendiente">Pendiente</option>
                <option value="abonada">Abonada</option>
                <option value="cancelada">Cancelada</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {isLoading && (
        <div className="flex items-center gap-2 py-8">
          <Spinner />
          <span className="text-muted-foreground">Cargando facturas...</span>
        </div>
      )}

      {data && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              {data.total} resultados
            </span>
          </div>

          <FacturaTable
            items={data.items}
            onView={setDetailItem}
            onAbonar={handleAbonar}
          />

          <div className="flex flex-wrap gap-2">
            {data.items
              .filter((f) => f.estado === 'pendiente')
              .map((f) => (
                <AbonarButton
                  key={f.id}
                  factura={f}
                  onAbonar={handleAbonar}
                  isLoading={abonar.isPending}
                />
              ))}
          </div>
        </div>
      )}

      <FacturaDetail item={detailItem} onClose={() => setDetailItem(null)} />
    </div>
  );
}
