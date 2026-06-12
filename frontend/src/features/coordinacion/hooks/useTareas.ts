import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/tareas.api';
import type { Tarea, TareaFilters } from '../types/tareas.types';

const NON_TERMINAL_STATES = ['pendiente', 'en_proceso'] as const;

function hasNonTerminal(tareas?: Tarea[]): boolean {
  if (!tareas) return false;
  return tareas.some((t) => (NON_TERMINAL_STATES as readonly string[]).includes(t.estado));
}

const TAREAS_KEYS = {
  all: ['coordinacion', 'tareas'] as const,
  misTareas: (filters?: TareaFilters) =>
    ['coordinacion', 'tareas', 'mis-tareas', filters] as const,
  admin: (filters?: TareaFilters) =>
    ['coordinacion', 'tareas', 'admin', filters] as const,
};

export function useMisTareas(filters?: TareaFilters) {
  return useQuery<Tarea[]>({
    queryKey: TAREAS_KEYS.misTareas(filters),
    queryFn: () => api.getMisTareas(filters),
    staleTime: 10 * 1000,
    enabled: !!getAccessToken(),
    refetchInterval: (query) => {
      const data = query.state.data;
      return hasNonTerminal(data) ? 30_000 : false;
    },
  });
}

export function useTareasAdmin(filters?: TareaFilters) {
  return useQuery<Tarea[]>({
    queryKey: TAREAS_KEYS.admin(filters),
    queryFn: () => api.getTareasAdmin(filters),
    staleTime: 30 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useAsignarTarea() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.asignarTarea,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'tareas', 'mis-tareas'] });
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'tareas', 'admin'] });
    },
  });
}

export function useActualizarEstadoTarea() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, estado, comentario }: { id: string; estado: string; comentario?: string }) =>
      api.actualizarEstadoTarea(id, { estado, comentario }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'tareas'] });
    },
  });
}
