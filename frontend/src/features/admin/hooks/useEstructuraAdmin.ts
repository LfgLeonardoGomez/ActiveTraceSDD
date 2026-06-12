import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/estructura.api';
import type {
  Carrera,
  CarreraCreate,
  Cohorte,
  CohorteCreate,
  Materia,
  MateriaCreate,
  EstructuraFilters,
} from '../types/estructura.types';

const ESTRUCTURA_KEYS = {
  carreras: (filters?: EstructuraFilters) => ['admin', 'carreras', filters] as const,
  cohortes: (filters?: EstructuraFilters) => ['admin', 'cohortes', filters] as const,
  materias: (filters?: EstructuraFilters) => ['admin', 'materias', filters] as const,
};

export function useCarrerasAdmin(filters?: EstructuraFilters) {
  return useQuery<Carrera[]>({
    queryKey: ESTRUCTURA_KEYS.carreras(filters),
    queryFn: () => api.getCarrerasAdmin(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCrearCarreraAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearCarreraAdmin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'carreras'] });
    },
  });
}

export function useActualizarCarreraAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CarreraCreate> }) =>
      api.actualizarCarreraAdmin(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'carreras'] });
    },
  });
}

export function useCohortesAdmin(filters?: EstructuraFilters) {
  return useQuery<Cohorte[]>({
    queryKey: ESTRUCTURA_KEYS.cohortes(filters),
    queryFn: () => api.getCohortesAdmin(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCrearCohorteAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearCohorteAdmin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'cohortes'] });
    },
  });
}

export function useActualizarCohorteAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CohorteCreate> }) =>
      api.actualizarCohorteAdmin(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'cohortes'] });
    },
  });
}

export function useMateriasAdmin(filters?: EstructuraFilters) {
  return useQuery<Materia[]>({
    queryKey: ESTRUCTURA_KEYS.materias(filters),
    queryFn: () => api.getMateriasAdmin(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCrearMateriaAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearMateriaAdmin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'materias'] });
    },
  });
}

export function useActualizarMateriaAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<MateriaCreate> }) =>
      api.actualizarMateriaAdmin(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'materias'] });
    },
  });
}
