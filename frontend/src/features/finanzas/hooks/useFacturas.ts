import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/facturas.api';
import type { Factura, FacturaCreate, FacturaFilters } from '../types/facturas.types';

const FACTURAS_KEYS = {
  all: (filters?: FacturaFilters) => ['finanzas', 'facturas', filters] as const,
};

export function useFacturas(filters?: FacturaFilters) {
  return useQuery<{ items: Factura[]; total: number }>({
    queryKey: FACTURAS_KEYS.all(filters),
    queryFn: () => api.getFacturas(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCrearFactura() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearFactura,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finanzas', 'facturas'] });
    },
  });
}

export function useAbonarFactura() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.abonarFactura,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finanzas', 'facturas'] });
    },
  });
}

export function useEliminarFactura() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.eliminarFactura,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finanzas', 'facturas'] });
    },
  });
}
