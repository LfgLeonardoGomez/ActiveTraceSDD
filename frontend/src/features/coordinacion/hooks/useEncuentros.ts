import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/encuentros.api';
import type { Encuentro, Guardia, EncuentroFilters, GuardiaFilters } from '../types/encuentros.types';

const ENCUENTROS_KEYS = {
  all: ['coordinacion', 'encuentros'] as const,
  list: (filters?: EncuentroFilters) =>
    ['coordinacion', 'encuentros', 'list', filters] as const,
  contenidoAula: (filters?: Record<string, string>) =>
    ['coordinacion', 'encuentros', 'contenido-aula', filters] as const,
  guardias: (filters?: GuardiaFilters) =>
    ['coordinacion', 'encuentros', 'guardias', filters] as const,
};

export function useEncuentros(filters?: EncuentroFilters) {
  return useQuery<Encuentro[]>({
    queryKey: ENCUENTROS_KEYS.list(filters),
    queryFn: () => api.getEncuentros(filters as Record<string, string> | undefined),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCrearRecurrente() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearRecurrente,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'encuentros', 'list'] });
    },
  });
}

export function useCrearEncuentro() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearEncuentro,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'encuentros', 'list'] });
    },
  });
}

export function useEditarEncuentro() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Encuentro> }) =>
      api.editarEncuentro(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'encuentros', 'list'] });
    },
  });
}

export function useContenidoAula(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ENCUENTROS_KEYS.contenidoAula(filters),
    queryFn: () => api.getContenidoAula(filters),
    enabled: !!getAccessToken() && !!filters && Object.keys(filters).length > 0,
  });
}

export function useGuardias(filters?: GuardiaFilters) {
  return useQuery<Guardia[]>({
    queryKey: ENCUENTROS_KEYS.guardias(filters),
    queryFn: () => api.getGuardias(filters as Record<string, string> | undefined),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useRegistrarGuardia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.registrarGuardia,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'encuentros', 'guardias'] });
    },
  });
}
