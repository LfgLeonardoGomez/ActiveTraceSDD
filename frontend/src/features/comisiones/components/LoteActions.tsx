import { useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { useComunicacionAction } from '../hooks/useComunicaciones';
import { usePermissions } from '@/shared/hooks/usePermissions';
import { CheckCircle, XCircle } from 'lucide-react';

interface LoteActionsProps {
  loteId: string;
  loteEstado: string;
  itemCount: number;
}

export function LoteActions({ loteId, loteEstado, itemCount }: LoteActionsProps) {
  const { can } = usePermissions();
  const actionMutation = useComunicacionAction(loteId);
  const [confirmAction, setConfirmAction] = useState<'approve' | 'cancel' | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const canApprove = can('comunicacion:aprobar');
  const isPending = loteEstado === 'pendiente';

  if (!canApprove || !isPending) return null;

  const handleAction = async (action: 'approve' | 'cancel') => {
    setMessage(null);
    try {
      await actionMutation.mutateAsync({ action });
      setMessage({
        type: 'success',
        text: action === 'approve' ? 'Lote aprobado' : 'Lote cancelado',
      });
    } catch {
      setMessage({
        type: 'error',
        text: `Error al ${action === 'approve' ? 'aprobar' : 'cancelar'} el lote. Intentá de nuevo.`,
      });
    } finally {
      setConfirmAction(null);
    }
  };

  return (
    <div className="flex items-center gap-3">
      <Button
        size="sm"
        onClick={() => setConfirmAction('approve')}
        isLoading={actionMutation.isPending && confirmAction === 'approve'}
      >
        <CheckCircle className="mr-1.5 h-4 w-4" />
        Aprobar lote
      </Button>
      <Button
        variant="destructive"
        size="sm"
        onClick={() => setConfirmAction('cancel')}
        isLoading={actionMutation.isPending && confirmAction === 'cancel'}
      >
        <XCircle className="mr-1.5 h-4 w-4" />
        Cancelar lote
      </Button>

      {confirmAction === 'approve' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-neutral-900">Confirmar aprobación</h3>
            <p className="mt-2 text-sm text-neutral-600">
              ¿Aprobar el envío a {itemCount} destinatario{itemCount !== 1 ? 's' : ''}?
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="outline" onClick={() => setConfirmAction(null)}>
                Cancelar
              </Button>
              <Button onClick={() => handleAction('approve')} isLoading={actionMutation.isPending}>
                Confirmar
              </Button>
            </div>
          </div>
        </div>
      )}

      {confirmAction === 'cancel' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-neutral-900">Confirmar cancelación</h3>
            <p className="mt-2 text-sm text-neutral-600">
              ¿Cancelar el envío a {itemCount} destinatario{itemCount !== 1 ? 's' : ''}? Esta
              acción no se puede deshacer.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="outline" onClick={() => setConfirmAction(null)}>
                Volver
              </Button>
              <Button
                variant="destructive"
                onClick={() => handleAction('cancel')}
                isLoading={actionMutation.isPending}
              >
                Cancelar lote
              </Button>
            </div>
          </div>
        </div>
      )}

      {message && (
        <div
          className={`rounded-md px-3 py-1.5 text-xs ${
            message.type === 'success'
              ? 'bg-success-50 text-success-600'
              : 'bg-danger-50 text-danger-600'
          }`}
        >
          {message.text}
        </div>
      )}
    </div>
  );
}
