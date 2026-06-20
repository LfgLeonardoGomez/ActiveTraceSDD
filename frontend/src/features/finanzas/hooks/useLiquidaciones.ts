import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/liquidaciones.api';
import type { LiquidacionView, LiquidacionHistorialEntry, HistorialFilters } from '../types/liquidaciones.types';

const LIQUIDACIONES_KEYS = {
  all: ['finanzas', 'liquidacion'] as const,
  view: (cohorteId: string, periodo: string) => ['finanzas', 'liquidacion', cohorteId, periodo] as const,
  historial: (filters?: HistorialFilters) => ['finanzas', 'historial', filters] as const,
};

export function useLiquidacion(cohorteId: string, periodo: string) {
  return useQuery<LiquidacionView>({
    queryKey: LIQUIDACIONES_KEYS.view(cohorteId, periodo),
    queryFn: () => api.getLiquidacion(cohorteId, periodo),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken() && !!cohorteId && !!periodo,
  });
}

export function useCerrarLiquidacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ cohorteId, periodo }: { cohorteId: string; periodo: string }) =>
      api.cerrarLiquidacion(cohorteId, periodo),
    onSuccess: (_, { cohorteId, periodo }) => {
      queryClient.invalidateQueries({ queryKey: LIQUIDACIONES_KEYS.view(cohorteId, periodo) });
      queryClient.invalidateQueries({ queryKey: ['finanzas', 'historial'] });
    },
  });
}

export function useHistorial(filters?: HistorialFilters) {
  return useQuery<{ items: LiquidacionHistorialEntry[]; total: number; page: number; page_size: number }>({
    queryKey: LIQUIDACIONES_KEYS.historial(filters),
    queryFn: () => api.getHistorial(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

// NOTE: useCohortesLiquidacion removed — /api/v1/liquidaciones/cohortes does not exist.
// Cohorte lookup should be wired to the comisiones/estructura-academica module endpoint
// once that endpoint is available.
