import { useState, useCallback } from 'react';
import { useComunicacionEstado, useComunicacionAction } from '../hooks/useComunicaciones';
import { Spinner } from '@/shared/components/ui/Spinner';
import { Button } from '@/shared/components/ui/Button';
import { CheckCircle, XCircle, Clock, Send, AlertTriangle, RefreshCw, Ban, RotateCcw } from 'lucide-react';

interface ComunicacionTrackingProps {
  loteId: string;
  onBack: () => void;
}

export function ComunicacionTracking({ loteId, onBack }: ComunicacionTrackingProps) {
  const { data, isLoading, isError, refetch, isFetching } = useComunicacionEstado(loteId);
  const actionMutation = useComunicacionAction(loteId);
  const [confirming, setConfirming] = useState<{ id: string; alumno: string; action: 'cancel' | 'retry' } | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-md bg-danger-50 p-4 text-sm text-danger-600">
        <p>Error al cargar el estado de la comunicación</p>
        <button
          onClick={() => refetch()}
          className="mt-2 font-medium text-danger-700 underline hover:text-danger-800"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!data) return null;

  const { estado, items } = data;
  const total = items.length;
  const pendientes = items.filter((i) => i.estado === 'pendiente').length;
  const enviando = items.filter((i) => i.estado === 'enviando').length;
  const enviados = items.filter((i) => i.estado === 'enviado').length;
  const fallidos = items.filter((i) => i.estado === 'fallido').length;
  const cancelados = items.filter((i) => i.estado === 'cancelado').length;
  const completados = enviados + fallidos + cancelados;
  const progress = total > 0 ? Math.round((completados / total) * 100) : 0;
  const isTerminal = estado === 'completado' || estado === 'cancelado';

  const stateBadge = () => {
    const styles: Record<string, string> = {
      pendiente: 'bg-neutral-100 text-neutral-700',
      enviando: 'bg-blue-50 text-blue-700',
      enviado: 'bg-success-50 text-success-700',
      fallido: 'bg-danger-50 text-danger-700',
      cancelado: 'bg-warning-50 text-warning-700',
      completado: 'bg-success-50 text-success-700',
    };
    return styles[estado] ?? 'bg-neutral-100 text-neutral-700';
  };

  const itemBadge = (estadoItem: string) => {
    const styles: Record<string, string> = {
      pendiente: 'bg-neutral-100 text-neutral-600',
      enviando: 'bg-blue-50 text-blue-600',
      enviado: 'bg-success-50 text-success-600',
      fallido: 'bg-danger-50 text-danger-600',
      cancelado: 'bg-warning-50 text-warning-600',
    };
    return styles[estadoItem] ?? 'bg-neutral-100 text-neutral-600';
  };

  const handleIndividualAction = useCallback(
    (comunicacionId: string, action: 'cancel' | 'retry') => {
      actionMutation.mutate(
        { action, comunicacionId },
        {
          onSettled: () => setConfirming(null),
        },
      );
    },
    [actionMutation],
  );

  const isActionable = (estadoItem: string) =>
    estadoItem === 'pendiente' || estadoItem === 'enviando' || estadoItem === 'fallido';

  const itemIcon = (estadoItem: string) => {
    switch (estadoItem) {
      case 'pendiente':
        return <Clock className="h-3.5 w-3.5" />;
      case 'enviando':
        return <Send className="h-3.5 w-3.5" />;
      case 'enviado':
        return <CheckCircle className="h-3.5 w-3.5" />;
      case 'fallido':
        return <XCircle className="h-3.5 w-3.5" />;
      case 'cancelado':
        return <AlertTriangle className="h-3.5 w-3.5" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${stateBadge()}`}
          >
            {estado === 'enviando' && <Spinner size="sm" />}
            {estado === 'pendiente' && <Clock className="h-4 w-4" />}
            {estado === 'completado' && <CheckCircle className="h-4 w-4" />}
            {estado === 'cancelado' && <AlertTriangle className="h-4 w-4" />}
            Estado: {estado === 'completado' ? 'Completado' : estado.charAt(0).toUpperCase() + estado.slice(1)}
          </span>
          {isFetching && !isLoading && (
            <span className="flex items-center gap-1 text-xs text-neutral-500">
              <RefreshCw className="h-3 w-3 animate-spin" />
              Actualizando...
            </span>
          )}
        </div>
      </div>

      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs text-neutral-500">
          <span>Progreso</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-200">
          <div
            className={`h-full rounded-full transition-all ${
              estado === 'cancelado' ? 'bg-warning-500' : 'bg-primary-600'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <div className="rounded-md bg-neutral-50 p-3 text-center">
          <p className="text-lg font-bold text-neutral-700">{total}</p>
          <p className="text-xs text-neutral-500">Total</p>
        </div>
        <div className="rounded-md bg-neutral-50 p-3 text-center">
          <p className="text-lg font-bold text-neutral-500">{pendientes}</p>
          <p className="text-xs text-neutral-500">Pendientes</p>
        </div>
        <div className="rounded-md bg-blue-50 p-3 text-center">
          <p className="text-lg font-bold text-blue-700">{enviando}</p>
          <p className="text-xs text-blue-600">Enviando</p>
        </div>
        <div className="rounded-md bg-success-50 p-3 text-center">
          <p className="text-lg font-bold text-success-700">{enviados}</p>
          <p className="text-xs text-success-600">Enviados</p>
        </div>
        <div className="rounded-md bg-danger-50 p-3 text-center">
          <p className="text-lg font-bold text-danger-700">{fallidos}</p>
          <p className="text-xs text-danger-600">Fallidos</p>
        </div>
      </div>

      {isTerminal && (
        <div
          className={`rounded-md p-4 text-sm ${
            estado === 'cancelado' ? 'bg-warning-50 text-warning-700' : 'bg-success-50 text-success-700'
          }`}
        >
          <div className="flex items-center gap-2">
            {estado === 'cancelado' ? (
              <>
                <AlertTriangle className="h-5 w-5" />
                <span>Lote cancelado por el aprobador</span>
              </>
            ) : fallidos > 0 ? (
              <>
                <AlertTriangle className="h-5 w-5" />
                <span>Algunos mensajes no se entregaron</span>
              </>
            ) : (
              <>
                <CheckCircle className="h-5 w-5" />
                <span>Todos los mensajes fueron enviados correctamente</span>
              </>
            )}
          </div>
        </div>
      )}

      {/* ── Confirmation dialog ── */}
      {confirming && (
        <div className="rounded-md border border-neutral-200 bg-neutral-50 p-4">
          <p className="text-sm text-neutral-800">
            {confirming.action === 'cancel'
              ? `¿Cancelar el envío a ${confirming.alumno}?`
              : `¿Reintentar el envío a ${confirming.alumno}?`}
          </p>
          <div className="mt-3 flex gap-2">
            <Button
              size="sm"
              variant={confirming.action === 'cancel' ? 'danger' : 'primary'}
              onClick={() => handleIndividualAction(confirming.id, confirming.action)}
              disabled={actionMutation.isPending}
            >
              {actionMutation.isPending ? (
                <>
                  <Spinner size="sm" /> Procesando...
                </>
              ) : confirming.action === 'cancel' ? (
                <>
                  <Ban className="h-4 w-4" /> Cancelar
                </>
              ) : (
                <>
                  <RotateCcw className="h-4 w-4" /> Reintentar
                </>
              )}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setConfirming(null)}
              disabled={actionMutation.isPending}
            >
              Cerrar
            </Button>
          </div>
        </div>
      )}

      {items.length > 0 && (
        <div className="overflow-x-auto rounded-md border border-neutral-200">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                  Destinatario
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                  Email
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                  Estado
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium uppercase text-neutral-500">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-200">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-neutral-50">
                  <td className="px-3 py-2 font-medium text-neutral-900">{item.alumno_nombre}</td>
                  <td className="px-3 py-2 text-neutral-600">{item.alumno_email}</td>
                  <td className="px-3 py-2">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${itemBadge(item.estado)}`}
                    >
                      {itemIcon(item.estado)}
                      {item.estado.charAt(0).toUpperCase() + item.estado.slice(1)}
                    </span>
                    {item.error && (
                      <span className="ml-2 text-xs text-danger-500" title={item.error}>
                        ({item.error})
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex gap-1">
                      {(item.estado === 'pendiente' || item.estado === 'enviando') && (
                        <button
                          onClick={() =>
                            setConfirming({
                              id: item.id,
                              alumno: item.alumno_nombre,
                              action: 'cancel',
                            })
                          }
                          className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium text-warning-700 hover:bg-warning-50 disabled:opacity-50"
                          disabled={actionMutation.isPending}
                          title="Cancelar mensaje"
                        >
                          <Ban className="h-3 w-3" />
                          Cancelar
                        </button>
                      )}
                      {item.estado === 'fallido' && (
                        <button
                          onClick={() =>
                            setConfirming({
                              id: item.id,
                              alumno: item.alumno_nombre,
                              action: 'retry',
                            })
                          }
                          className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium text-primary-700 hover:bg-primary-50 disabled:opacity-50"
                          disabled={actionMutation.isPending}
                          title="Reintentar envío"
                        >
                          <RotateCcw className="h-3 w-3" />
                          Reintentar
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isTerminal && (
        <div className="flex justify-center">
          <button
            onClick={onBack}
            className="text-sm font-medium text-primary-600 hover:underline"
          >
            Volver
          </button>
        </div>
      )}
    </div>
  );
}
