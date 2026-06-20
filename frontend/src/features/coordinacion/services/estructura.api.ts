import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type { Carrera, Cohorte, Programa, Evaluacion } from '../types/estructura.types';

// Carreras / Cohortes live in the estructura router mounted under /api/v1/admin.
export async function getCarreras(): Promise<Carrera[]> {
  const { data } = await api.get<Carrera[] | Paginated<Carrera>>('/api/v1/admin/carreras');
  return toList(data);
}

export async function crearCarrera(payload: Partial<Carrera>): Promise<Carrera> {
  const { data } = await api.post<Carrera>('/api/v1/admin/carreras', payload);
  return data;
}

export async function actualizarCarrera(id: string, payload: Partial<Carrera>): Promise<Carrera> {
  const { data } = await api.put<Carrera>(`/api/v1/admin/carreras/${id}`, payload);
  return data;
}

export async function getCohortes(filters?: Record<string, string>): Promise<Cohorte[]> {
  const { data } = await api.get<Cohorte[] | Paginated<Cohorte>>('/api/v1/admin/cohortes', { params: filters });
  return toList(data);
}

export async function crearCohorte(payload: Partial<Cohorte>): Promise<Cohorte> {
  const { data } = await api.post<Cohorte>('/api/v1/admin/cohortes', payload);
  return data;
}

export async function actualizarCohorte(id: string, payload: Partial<Cohorte>): Promise<Cohorte> {
  const { data } = await api.put<Cohorte>(`/api/v1/admin/cohortes/${id}`, payload);
  return data;
}

// Programas live in their own router at /api/programas.
export async function getProgramas(): Promise<Programa[]> {
  const { data } = await api.get<Programa[] | Paginated<Programa>>('/api/programas/');
  return toList(data);
}

export async function subirPrograma(formData: FormData): Promise<Programa> {
  const { data } = await api.post<Programa>('/api/programas/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function eliminarPrograma(id: string): Promise<void> {
  await api.delete(`/api/programas/${id}`);
}

export function descargarPrograma(id: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? '';
  return `${base}/api/programas/${id}/download`;
}

// Evaluaciones are the coloquios entity, served by the coloquios router.
export async function getEvaluaciones(filters?: Record<string, string>): Promise<Evaluacion[]> {
  const { data } = await api.get<Evaluacion[] | Paginated<Evaluacion>>('/api/coloquios/', { params: filters });
  return toList(data);
}

export async function crearEvaluacion(payload: Partial<Evaluacion>): Promise<Evaluacion> {
  const { data } = await api.post<Evaluacion>('/api/coloquios/', payload);
  return data;
}

export async function actualizarEvaluacion(id: string, payload: Partial<Evaluacion>): Promise<Evaluacion> {
  const { data } = await api.patch<Evaluacion>(`/api/coloquios/${id}`, payload);
  return data;
}
