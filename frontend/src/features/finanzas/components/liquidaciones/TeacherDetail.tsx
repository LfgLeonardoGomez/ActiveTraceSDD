import { X } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
import type { LiquidacionItem } from '../../types/liquidaciones.types';

interface TeacherDetailProps {
  item: LiquidacionItem | null;
  onClose: () => void;
}

function formatCurrency(v: number): string {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(v);
}

export default function TeacherDetail({ item, onClose }: TeacherDetailProps) {
  if (!item) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end bg-black/30 p-4 backdrop-blur-sm sm:items-center sm:justify-center">
      <Card className="w-full max-w-lg animate-in slide-in-from-bottom-4">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-lg">{item.docente_nombre}</CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Cerrar">
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground">Rol: {item.rol}</div>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-md bg-muted p-3">
              <div className="text-xs text-muted-foreground">Salario base</div>
              <div className="text-lg font-semibold tabular-nums">{formatCurrency(item.salario_base)}</div>
            </div>
            <div className="rounded-md bg-muted p-3">
              <div className="text-xs text-muted-foreground">Salario plus</div>
              <div className="text-lg font-semibold tabular-nums">{formatCurrency(item.salario_plus)}</div>
            </div>
            <div className="rounded-md bg-muted p-3">
              <div className="text-xs text-muted-foreground">Comisiones</div>
              <div className="text-lg font-semibold tabular-nums">{formatCurrency(item.comisiones)}</div>
            </div>
            <div className="rounded-md bg-primary-50 p-3">
              <div className="text-xs text-primary-700">Total</div>
              <div className="text-lg font-bold tabular-nums text-primary-700">{formatCurrency(item.total)}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
