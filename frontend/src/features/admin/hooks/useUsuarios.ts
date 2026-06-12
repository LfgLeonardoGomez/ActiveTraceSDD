import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '@/shared/services/api';
import * as api from '../services/usuarios.api';
import type { Usuario, UsuarioUpdate, UsuarioFilters } from '../types/usuarios.types';

const USUARIOS_KEYS = {
  all: (filters?: UsuarioFilters) => ['admin', 'usuarios', filters] as const,
};

export function useUsuariosAdmin(filters?: UsuarioFilters) {
  return useQuery<{ items: Usuario[]; total: number }>({
    queryKey: USUARIOS_KEYS.all(filters),
    queryFn: () => api.getUsuariosAdmin(filters),
    staleTime: 5 * 60 * 1000,
    enabled: !!getAccessToken(),
  });
}

export function useActualizarUsuarioAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UsuarioUpdate }) =>
      api.actualizarUsuarioAdmin(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'usuarios'] });
    },
  });
}
