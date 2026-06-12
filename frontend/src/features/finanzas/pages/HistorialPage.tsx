import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import { Spinner } from '@/shared/components/ui/Spinner';
import { useHistorial } from '../hooks/useLiquidaciones';
import type { HistorialFilters } from '../types/liquidaciones.types';

export default function HistorialPage() {
  const [filters, setFilters] = useState<HistorialFilters>({ page: 1, page_size: 50 });
  const { data, isLoading } = useHistorial(filters);

  const handleFilterChange = (key: keyof HistorialFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined, page: 1 }));
  };

  function formatCurrency(v: number): string {
    return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(v);
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold tracking-tight">Historial de liquidaciones</h1>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-3">
            <Input
              label="Mes"
              type="month"
              value={filters.mes ?? ''}
              onChange={(e) => handleFilterChange('mes', e.target.value)}
              className="w-48"
            />
            <Input
              label="Cohorte"
              placeholder="Buscar cohorte..."
              value={filters.cohorte_id ?? ''}
              onChange={(e) => handleFilterChange('cohorte_id', e.target.value)}
              className="w-64"
            />
          </div>
        </CardContent>
      </Card>

      {isLoading && (
        <div className="flex items-center gap-2 py-8">
          <Spinner />
          <span className="text-muted-foreground">Cargando historial...</span>
        </div>
      )}

      {data && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Resultados ({data.total})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-hidden rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Período</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Cohorte</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Estado</th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">Sin factura</th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">Con factura</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Fecha cierre</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {data.items.map((item) => (
                    <tr key={item.id} className="hover:bg-muted/50">
                      <td className="px-4 py-3 font-medium">{item.periodo}</td>
                      <td className="px-4 py-3 text-muted-foreground">{item.cohorte_nombre}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            item.estado === 'abierto'
                              ? 'bg-emerald-100 text-emerald-700'
                              : 'bg-neutral-100 text-neutral-700'
                          }`}
                        >
                          {item.estado}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(item.total_sin_factura)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(item.total_con_factura)}</td>
                      <td className="px-4 py-3 text-muted-foreground">{item.fecha_cierre ?? '-'}</td>
                    </tr>
                  ))}
                  {data.items.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                        No se encontraron liquidaciones cerradas
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
