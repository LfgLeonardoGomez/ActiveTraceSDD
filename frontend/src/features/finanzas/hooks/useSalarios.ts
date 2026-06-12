import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/salarios.api';
import type { SalarioBase, SalarioBaseCreate, SalarioPlus, SalarioPlusCreate, SalarioFilters } from '../types/salarios.types';

const SALARIOS_KEYS = {
  base: (filters?: SalarioFilters) => ['finanzas', 'salario-base', filters] as const,
  plus: (filters?: SalarioFilters) => ['finanzas', 'salario-plus', filters] as const,
};

export function useSalarioBase(filters?: SalarioFilters) {
  return useQuery<SalarioBase[]>({
    queryKey: SALARIOS_KEYS.base(filters),
    queryFn: () => api.getSalarioBase(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCrearSalarioBase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearSalarioBase,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finanzas', 'salario-base'] });
    },
  });
}

export function useActualizarSalarioBase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<SalarioBaseCreate> }) =>
      api.actualizarSalarioBase(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finanzas', 'salario-base'] });
    },
  });
}

export function useEliminarSalarioBase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.eliminarSalarioBase,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finanzas', 'salario-base'] });
    },
  });
}

export function useSalarioPlus(filters?: SalarioFilters) {
  return useQuery<SalarioPlus[]>({
    queryKey: SALARIOS_KEYS.plus(filters),
    queryFn: () => api.getSalarioPlus(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useCrearSalarioPlus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.crearSalarioPlus,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finanzas', 'salario-plus'] });
    },
  });
}

export function useActualizarSalarioPlus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<SalarioPlusCreate> }) =>
      api.actualizarSalarioPlus(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finanzas', 'salario-plus'] });
    },
  });
}

export function useEliminarSalarioPlus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.eliminarSalarioPlus,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finanzas', 'salario-plus'] });
    },
  });
}
