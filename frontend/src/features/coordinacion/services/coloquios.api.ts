import api from '@/shared/services/api';
import type { MetricasColoquios, Convocatoria, ImportResult, Reserva } from '../types/coloquios.types';

export async function getMetricas(): Promise<MetricasColoquios> {
  const { data } = await api.get<MetricasColoquios>('/api/v1/coloquios/metricas');
  return data;
}

export async function getConvocatorias(filters?: Record<string, string>): Promise<Convocatoria[]> {
  const { data } = await api.get<Convocatoria[]>('/api/v1/coloquios', { params: filters });
  return data;
}

export async function crearConvocatoria(payload: Partial<Convocatoria>): Promise<Convocatoria> {
  const { data } = await api.post<Convocatoria>('/api/v1/coloquios', payload);
  return data;
}

export async function getConvocatoriaDetail(id: string): Promise<Convocatoria> {
  const { data } = await api.get<Convocatoria>(`/api/v1/coloquios/${id}`);
  return data;
}

export async function importarAlumnos(formData: FormData): Promise<ImportResult> {
  const { data } = await api.post<ImportResult>('/api/v1/coloquios/importar-alumnos', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function getAdminConvocatorias(): Promise<Convocatoria[]> {
  const { data } = await api.get<Convocatoria[]>('/api/v1/coloquios/admin');
  return data;
}

export async function cerrarConvocatoria(id: string): Promise<Convocatoria> {
  const { data } = await api.put<Convocatoria>(`/api/v1/coloquios/admin/${id}`);
  return data;
}

export async function getReservasActivas(): Promise<Reserva[]> {
  const { data } = await api.get<Reserva[]>('/api/v1/coloquios/reservas-activas');
  return data;
}
