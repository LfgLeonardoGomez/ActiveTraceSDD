import { Eye, CheckCircle2 } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import type { Factura } from '../../types/facturas.types';

interface FacturaTableProps {
  items: Factura[];
  onView: (item: Factura) => void;
  onAbonar: (item: Factura) => void;
}

function formatCurrency(v: number): string {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(v);
}

function statusBadge(estado: Factura['estado']) {
  const styles: Record<Factura['estado'], string> = {
    pendiente: 'bg-amber-100 text-amber-700',
    abonada: 'bg-emerald-100 text-emerald-700',
    cancelada: 'bg-neutral-100 text-neutral-700',
  };
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${styles[estado]}`}>{estado}</span>
  );
}

export default function FacturaTable({ items, onView, onAbonar }: FacturaTableProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Docente</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Período</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Monto</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Estado</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {items.map((item) => (
            <tr key={item.id} className="hover:bg-muted/50">
              <td className="px-4 py-3 font-medium">{item.docente_nombre}</td>
              <td className="px-4 py-3 text-muted-foreground">{item.periodo}</td>
              <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(item.monto)}</td>
              <td className="px-4 py-3">{statusBadge(item.estado)}</td>
              <td className="px-4 py-3 text-right">
                <div className="flex justify-end gap-1">
                  <Button variant="ghost" size="icon" onClick={() => onView(item)} aria-label="Ver detalle">
                    <Eye className="size-4" />
                  </Button>
                  {item.estado === 'pendiente' && (
                    <Button variant="ghost" size="icon" onClick={() => onAbonar(item)} aria-label="Abonar">
                      <CheckCircle2 className="size-4 text-emerald-600" />
                    </Button>
                  )}
                </div>
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                No hay facturas registradas
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
