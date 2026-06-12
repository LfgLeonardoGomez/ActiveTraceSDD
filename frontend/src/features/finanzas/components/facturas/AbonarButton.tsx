import { CheckCircle2 } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import type { Factura } from '../../types/facturas.types';

interface AbonarButtonProps {
  factura: Factura;
  onAbonar: (factura: Factura) => void;
  isLoading?: boolean;
}

export default function AbonarButton({ factura, onAbonar, isLoading }: AbonarButtonProps) {
  if (factura.estado !== 'pendiente') {
    return null;
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={() => onAbonar(factura)}
      isLoading={isLoading}
      className="gap-1 text-emerald-700 hover:bg-emerald-50 hover:text-emerald-800"
    >
      <CheckCircle2 className="size-4" />
      Abonar
    </Button>
  );
}
