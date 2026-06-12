import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/estructura.api';
import type { Carrera, Cohorte, Programa, Evaluacion } from '../types/estructura.types';

const ESTRUCTURA_KEYS = {
  all: ['coordinacion', 'estructura'] as const,
  carreras: () => ['coordinacion', 'estructura', 'carreras'] as const,
  cohortes: (filters?: Record<string, string>) =>
    ['coordinacion', 'estructura', 'cohortes', filters] as const,
  programas: () => ['coordinacion', 'estructura', 'programas'] as const,
  evaluaciones: (filters?: Record<string, string>) =>
    ['coordinacion', 'estructura', 'evaluaciones', filters] as const,
};

export function useCarreras() {
  return useQuery<Carrera[]>({
    queryKey: ESTRUCTURA_KEYS.carreras(),
    queryFn: api.getCarreras,
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCrearCarrera() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearCarrera,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ESTRUCTURA_KEYS.carreras() });
    },
  });
}

export function useActualizarCarrera() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Carrera> }) =>
      api.actualizarCarrera(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ESTRUCTURA_KEYS.carreras() });
    },
  });
}

export function useCohortes(filters?: Record<string, string>) {
  return useQuery<Cohorte[]>({
    queryKey: ESTRUCTURA_KEYS.cohortes(filters),
    queryFn: () => api.getCohortes(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCrearCohorte() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearCohorte,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ESTRUCTURA_KEYS.cohortes() });
    },
  });
}

export function useActualizarCohorte() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Cohorte> }) =>
      api.actualizarCohorte(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ESTRUCTURA_KEYS.cohortes() });
    },
  });
}

export function useProgramas() {
  return useQuery<Programa[]>({
    queryKey: ESTRUCTURA_KEYS.programas(),
    queryFn: api.getProgramas,
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useSubirPrograma() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.subirPrograma,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ESTRUCTURA_KEYS.programas() });
    },
  });
}

export function useEliminarPrograma() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.eliminarPrograma,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ESTRUCTURA_KEYS.programas() });
    },
  });
}

export function useEvaluaciones(filters?: Record<string, string>) {
  return useQuery<Evaluacion[]>({
    queryKey: ESTRUCTURA_KEYS.evaluaciones(filters),
    queryFn: () => api.getEvaluaciones(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCrearEvaluacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearEvaluacion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ESTRUCTURA_KEYS.evaluaciones() });
    },
  });
}

export function useActualizarEvaluacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Evaluacion> }) =>
      api.actualizarEvaluacion(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ESTRUCTURA_KEYS.evaluaciones() });
    },
  });
}
