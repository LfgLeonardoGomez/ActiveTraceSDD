import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../services/avisos.api';
import type { Aviso, AvisoFormData } from '../types/avisos.types';

const AVISOS_KEYS = {
  all: ['coordinacion', 'avisos'] as const,
  list: (filters?: Record<string, string>) =>
    ['coordinacion', 'avisos', 'list', filters] as const,
};

export function useAvisos(filters?: Record<string, string>) {
  return useQuery<Aviso[]>({
    queryKey: AVISOS_KEYS.list(filters),
    queryFn: () => api.getAvisos(filters),
    staleTime: 5 * 60 * 1000,
  });
}

export function useCrearAviso() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AvisoFormData) => api.crearAviso(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'avisos', 'list'] });
    },
  });
}

export function useEditarAviso() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<AvisoFormData> }) =>
      api.editarAviso(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'avisos', 'list'] });
    },
  });
}

export function useEliminarAviso() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.eliminarAviso(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'avisos', 'list'] });
    },
  });
}

export function useConfirmarAck() {
  return useMutation({
    mutationFn: (id: string) => api.confirmarAck(id),
  });
}
