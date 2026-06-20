import { X, FileText } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import type { Factura } from '../../types/facturas.types';

interface FacturaDetailProps {
  item: Factura | null;
  onClose: () => void;
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
              <span className="text-muted-foreground">Usuario ID</span>
              <span className="font-medium font-mono text-xs">{item.usuario_id}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Período</span>
              <span className="font-medium">{item.periodo}</span>
            </div>
            {item.detalle && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Detalle</span>
                <span className="font-medium">{item.detalle}</span>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Estado</span>
              <span className="font-medium capitalize">{item.estado}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Fecha carga</span>
              <span className="font-medium">{new Date(item.cargada_at).toLocaleDateString('es-AR')}</span>
            </div>
            {item.abonada_at && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Fecha pago</span>
                <span className="font-medium">{new Date(item.abonada_at).toLocaleDateString('es-AR')}</span>
              </div>
            )}
          </div>

          <a
            href={`/api/v1/facturas/${item.id}/archivo`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-md border border-border p-3 text-sm hover:bg-muted"
          >
            <FileText className="size-4 text-primary-600" />
            <span className="font-medium">Ver archivo adjunto</span>
          </a>
        </CardContent>
      </Card>
    </div>
  );
}
