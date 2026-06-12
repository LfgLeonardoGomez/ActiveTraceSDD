import { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';

interface CierreDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  periodo: string;
  isLoading?: boolean;
}

export default function CierreDialog({ open, onClose, onConfirm, periodo, isLoading }: CierreDialogProps) {
  const [checked, setChecked] = useState(false);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <AlertTriangle className="size-5 text-amber-500" />
            Cerrar liquidación
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Estás por cerrar la liquidación del período <strong>{periodo}</strong>. Una vez cerrada, no se podrán
            realizar más modificaciones.
          </p>
          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
              className="mt-0.5 size-4 rounded border-input text-primary-600 focus-visible:ring-primary-500"
            />
            <span>Confirmo que deseo cerrar esta liquidación de forma irreversible.</span>
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose} disabled={isLoading}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                onConfirm();
                setChecked(false);
              }}
              disabled={!checked || isLoading}
              isLoading={isLoading}
            >
              Cerrar liquidación
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
