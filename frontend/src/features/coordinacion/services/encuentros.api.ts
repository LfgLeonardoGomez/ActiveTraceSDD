import api from '@/shared/services/api';
import type { Encuentro, SerieRecurrenteRequest, Guardia } from '../types/encuentros.types';

export async function getEncuentros(filters?: Record<string, string>): Promise<Encuentro[]> {
  const { data } = await api.get<Encuentro[]>('/api/v1/encuentros', { params: filters });
  return data;
}

export async function crearEncuentro(payload: Partial<Encuentro>): Promise<Encuentro> {
  const { data } = await api.post<Encuentro>('/api/v1/encuentros', payload);
  return data;
}

export async function crearRecurrente(
  payload: SerieRecurrenteRequest,
): Promise<{ instancias: Encuentro[]; count: number }> {
  const { data } = await api.post<{ instancias: Encuentro[]; count: number }>(
    '/api/v1/encuentros/recurrente',
    payload,
  );
  return data;
}

export async function editarEncuentro(id: string, payload: Partial<Encuentro>): Promise<Encuentro> {
  const { data } = await api.put<Encuentro>(`/api/v1/encuentros/${id}`, payload);
  return data;
}

export async function getContenidoAula(filters?: Record<string, string>): Promise<unknown> {
  const { data } = await api.get('/api/v1/encuentros/contenido-aula', { params: filters });
  return data;
}

export async function getGuardias(filters?: Record<string, string>): Promise<Guardia[]> {
  const { data } = await api.get<Guardia[]>('/api/v1/encuentros/guardias', { params: filters });
  return data;
}

export async function registrarGuardia(payload: Partial<Guardia>): Promise<Guardia> {
  const { data } = await api.post<Guardia>('/api/v1/encuentros/guardias', payload);
  return data;
}
