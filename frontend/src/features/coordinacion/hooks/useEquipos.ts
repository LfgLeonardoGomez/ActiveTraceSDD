import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/equipos.api';
import type { Equipo, UsuarioDocente, Asignacion } from '../types/equipos.types';

const EQUIPOS_KEYS = {
  all: ['coordinacion', 'equipos'] as const,
  misEquipos: (filters?: Record<string, string>) =>
    ['coordinacion', 'equipos', 'mis-equipos', filters] as const,
  usuarios: () => ['coordinacion', 'equipos', 'usuarios'] as const,
  asignaciones: (filters?: Record<string, string>) =>
    ['coordinacion', 'equipos', 'asignaciones', filters] as const,
};

export function useMisEquipos(filters?: Record<string, string>) {
  return useQuery<Equipo[]>({
    queryKey: EQUIPOS_KEYS.misEquipos(filters),
    queryFn: () => api.getMisEquipos(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useUsuarios() {
  return useQuery<UsuarioDocente[]>({
    queryKey: EQUIPOS_KEYS.usuarios(),
    queryFn: api.getUsuarios,
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useAsignaciones(filters?: Record<string, string>) {
  return useQuery<Asignacion[]>({
    queryKey: EQUIPOS_KEYS.asignaciones(filters),
    queryFn: () => api.getAsignaciones(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCrearAsignacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearAsignacion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'equipos', 'asignaciones'] });
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'equipos', 'mis-equipos'] });
    },
  });
}

export function useAsignacionMasiva() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.asignacionMasiva,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'equipos', 'asignaciones'] });
    },
  });
}

export function useClonarEquipo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.clonarEquipo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'equipos', 'asignaciones'] });
    },
  });
}

export function useActualizarVigencia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.actualizarVigencia,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'equipos', 'asignaciones'] });
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'equipos', 'mis-equipos'] });
    },
  });
}

export function useCrearUsuario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearUsuario,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'equipos', 'usuarios'] });
    },
  });
}

export function useActualizarUsuario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<UsuarioDocente> }) =>
      api.actualizarUsuario(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coordinacion', 'equipos', 'usuarios'] });
    },
  });
}
