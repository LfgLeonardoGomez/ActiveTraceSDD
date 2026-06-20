import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type { Aviso, AvisoFormData } from '../types/avisos.types';

export async function getAvisos(filters?: Record<string, string>): Promise<Aviso[]> {
  const { data } = await api.get<Aviso[] | Paginated<Aviso>>('/api/avisos/', { params: filters });
  return toList(data);
}

export async function crearAviso(payload: AvisoFormData): Promise<Aviso> {
  const { data } = await api.post<Aviso>('/api/avisos/', payload);
  return data;
}

export async function editarAviso(id: string, payload: Partial<AvisoFormData>): Promise<Aviso> {
  const { data } = await api.put<Aviso>(`/api/avisos/${id}`, payload);
  return data;
}

export async function eliminarAviso(id: string): Promise<void> {
  await api.delete(`/api/avisos/${id}`);
}

export async function confirmarAck(id: string): Promise<void> {
  await api.post(`/api/avisos/${id}/confirmar`);
}
