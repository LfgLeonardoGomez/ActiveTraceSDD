import api from '@/shared/services/api';
import type { Aviso, AvisoFormData } from '../types/avisos.types';

export async function getAvisos(filters?: Record<string, string>): Promise<Aviso[]> {
  const { data } = await api.get<Aviso[]>('/api/v1/avisos', { params: filters });
  return data;
}

export async function crearAviso(payload: AvisoFormData): Promise<Aviso> {
  const { data } = await api.post<Aviso>('/api/v1/avisos', payload);
  return data;
}

export async function editarAviso(id: string, payload: Partial<AvisoFormData>): Promise<Aviso> {
  const { data } = await api.put<Aviso>(`/api/v1/avisos/${id}`, payload);
  return data;
}

export async function eliminarAviso(id: string): Promise<void> {
  await api.delete(`/api/v1/avisos/${id}`);
}

export async function confirmarAck(id: string): Promise<void> {
  await api.post(`/api/v1/avisos/${id}/ack`);
}
