import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/coloquios.api';
import type { MetricasColoquios, Convocatoria, ImportResult } from '../types/coloquios.types';

const COLOQUIOS_KEYS = {
  all: ['coordinacion', 'coloquios'] as const,
  metricas: () => ['coordinacion', 'coloquios', 'metricas'] as const,
  list: (filters?: Record<string, string>) =>
    ['coordinacion', 'coloquios', 'list', filters] as const,
  detail: (id: string) => ['coordinacion', 'coloquios', 'detail', id] as const,
  admin: () => ['coordinacion', 'coloquios', 'admin'] as const,
};

export function useMetricasColoquios() {
  return useQuery<MetricasColoquios>({
    queryKey: COLOQUIOS_KEYS.metricas(),
    queryFn: api.getMetricas,
    staleTime: 2 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useConvocatorias(filters?: Record<string, string>) {
  return useQuery<Convocatoria[]>({
    queryKey: COLOQUIOS_KEYS.list(filters),
    queryFn: () => api.getConvocatorias(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useConvocatoriaDetail(id: string) {
  return useQuery<Convocatoria>({
    queryKey: COLOQUIOS_KEYS.detail(id),
    queryFn: () => api.getConvocatoriaDetail(id),
    staleTime: 2 * 60 * 1000,
    enabled: !!getAccessToken() && !!id,
  });
}

export function useCrearConvocatoria() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearConvocatoria,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COLOQUIOS_KEYS.list() });
    },
  });
}

export function useImportarAlumnos() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.importarAlumnos,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COLOQUIOS_KEYS.metricas() });
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'coloquios', 'detail'] });
    },
  });
}

export function useCerrarConvocatoria() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.cerrarConvocatoria,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COLOQUIOS_KEYS.list() });
      queryClient.invalidateQueries({ queryKey: COLOQUIOS_KEYS.admin() });
    },
  });
}

export function useConvocatoriaAdmin() {
  return useQuery<Convocatoria[]>({
    queryKey: COLOQUIOS_KEYS.admin(),
    queryFn: api.getAdminConvocatorias,
    staleTime: 5 * 60 * 1000,
  });
}
