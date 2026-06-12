import { useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { useClearData } from '../hooks/useClearData';
import { AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface ClearDataDialogProps {
  materiaId: string;
  materiaNombre: string;
  open: boolean;
  onClose: () => void;
}

export function ClearDataDialog({ materiaId, materiaNombre, open, onClose }: ClearDataDialogProps) {
  const navigate = useNavigate();
  const mutation = useClearData(materiaId);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  if (!open) return null;

  const handleConfirm = async () => {
    setMessage(null);
    try {
      await mutation.mutateAsync();
      setMessage({ type: 'success', text: 'Datos vaciados correctamente' });
      setTimeout(() => {
        onClose();
        navigate('/comisiones');
      }, 1500);
    } catch {
      setMessage({ type: 'error', text: 'Error al vaciar los datos. Intentá de nuevo.' });
      setTimeout(() => {
        setMessage(null);
        onClose();
      }, 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-danger-50">
            <AlertTriangle className="h-5 w-5 text-danger-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-neutral-900">
              ¿Vaciar datos de {materiaNombre}?
            </h3>
          </div>
        </div>

        <p className="mt-4 text-sm text-neutral-600">
          Esta acción eliminará todas las calificaciones, umbrales, y análisis. No se puede
          deshacer.
        </p>

        {message && (
          <div
            className={`mt-4 rounded-md p-3 text-sm ${
              message.type === 'success'
                ? 'bg-success-50 text-success-600'
                : 'bg-danger-50 text-danger-600'
            }`}
          >
            {message.text}
          </div>
        )}

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="outline" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button
            variant="destructive"
            onClick={handleConfirm}
            isLoading={mutation.isPending}
          >
            Confirmar vaciado
          </Button>
        </div>
      </div>
    </div>
  );
}
