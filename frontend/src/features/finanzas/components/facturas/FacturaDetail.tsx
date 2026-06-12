import { X, FileText, Calendar } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import type { Factura } from '../../types/facturas.types';

interface FacturaDetailProps {
  item: Factura | null;
  onClose: () => void;
}

function formatCurrency(v: number): string {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(v);
}

export default function FacturaDetail({ item, onClose }: FacturaDetailProps) {
  if (!item) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end bg-black/30 p-4 backdrop-blur-sm sm:items-center sm:justify-center">
      <Card className="w-full max-w-md animate-in slide-in-from-bottom-4">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-lg">Detalle de factura</CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Cerrar">
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Docente</span>
              <span className="font-medium">{item.docente_nombre}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Período</span>
              <span className="font-medium">{item.periodo}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Monto</span>
              <span className="font-medium tabular-nums">{formatCurrency(item.monto)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Estado</span>
              <span className="font-medium capitalize">{item.estado}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Fecha subida</span>
              <span className="font-medium">{new Date(item.fecha_subida).toLocaleDateString('es-AR')}</span>
            </div>
            {item.fecha_pago && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Fecha pago</span>
                <span className="font-medium">{new Date(item.fecha_pago).toLocaleDateString('es-AR')}</span>
              </div>
            )}
          </div>

          {item.archivo_url && (
            <a
              href={item.archivo_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-md border border-border p-3 text-sm hover:bg-muted"
            >
              <FileText className="size-4 text-primary-600" />
              <span className="font-medium">Ver archivo adjunto</span>
            </a>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
