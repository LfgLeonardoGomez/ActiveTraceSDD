import api from '@/shared/services/api';
import type { Usuario, UsuarioUpdate, UsuarioFilters } from '../types/usuarios.types';

export async function getUsuariosAdmin(filters?: UsuarioFilters): Promise<{ items: Usuario[]; total: number }> {
  const { data } = await api.get('/api/admin/usuarios', { params: filters });
  return data;
}

export async function actualizarUsuarioAdmin(id: string, payload: UsuarioUpdate): Promise<Usuario> {
  const { data } = await api.patch<Usuario>(`/api/admin/usuarios/${id}`, payload);
  return data;
}
