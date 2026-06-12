import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  previewComunicacion,
  enviarComunicacion,
  getLoteStatus,
  loteAction,
} from '../services/comisiones.api';
import type {
  ComunicacionPreviewRequest,
  ComunicacionEnviarRequest,
  ComunicacionLote,
} from '../types/comisiones.types';

export function useComunicacionPreview() {
  return useMutation({
    mutationFn: (data: ComunicacionPreviewRequest) => previewComunicacion(data),
  });
}

export function useComunicacionEnviar() {
  return useMutation({
    mutationFn: (data: ComunicacionEnviarRequest) => enviarComunicacion(data),
  });
}

export function useComunicacionEstado(loteId: string | null) {
  return useQuery<ComunicacionLote>({
    queryKey: ['comunicaciones', 'lote', loteId],
    queryFn: () => getLoteStatus(loteId!),
    enabled: !!loteId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 5000;
      if (data.estado === 'completado' || data.estado === 'cancelado') return false;
      return 5000;
    },
  });
}

export function useComunicacionAction(loteId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      action,
      comunicacionId,
    }: {
      action: 'approve' | 'cancel' | 'retry';
      comunicacionId?: string;
    }) => loteAction(loteId, action, comunicacionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comunicaciones', 'lote', loteId] });
    },
  });
}
