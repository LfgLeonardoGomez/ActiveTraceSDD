import api from '@/shared/services/api';
import type { Carrera, Cohorte, Programa, Evaluacion } from '../types/estructura.types';

export async function getCarreras(): Promise<Carrera[]> {
  const { data } = await api.get<Carrera[]>('/api/v1/estructura/carreras');
  return data;
}

export async function crearCarrera(payload: Partial<Carrera>): Promise<Carrera> {
  const { data } = await api.post<Carrera>('/api/v1/estructura/carreras', payload);
  return data;
}

export async function actualizarCarrera(id: string, payload: Partial<Carrera>): Promise<Carrera> {
  const { data } = await api.put<Carrera>(`/api/v1/estructura/carreras/${id}`, payload);
  return data;
}

export async function getCohortes(filters?: Record<string, string>): Promise<Cohorte[]> {
  const { data } = await api.get<Cohorte[]>('/api/v1/estructura/cohortes', { params: filters });
  return data;
}

export async function crearCohorte(payload: Partial<Cohorte>): Promise<Cohorte> {
  const { data } = await api.post<Cohorte>('/api/v1/estructura/cohortes', payload);
  return data;
}

export async function actualizarCohorte(id: string, payload: Partial<Cohorte>): Promise<Cohorte> {
  const { data } = await api.put<Cohorte>(`/api/v1/estructura/cohortes/${id}`, payload);
  return data;
}

export async function getProgramas(): Promise<Programa[]> {
  const { data } = await api.get<Programa[]>('/api/v1/estructura/programas');
  return data;
}

export async function subirPrograma(formData: FormData): Promise<Programa> {
  const { data } = await api.post<Programa>('/api/v1/estructura/programas', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function eliminarPrograma(id: string): Promise<void> {
  await api.delete(`/api/v1/estructura/programas/${id}`);
}

export function descargarPrograma(id: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? '';
  return `${base}/api/v1/estructura/programas/${id}/download`;
}

export async function getEvaluaciones(filters?: Record<string, string>): Promise<Evaluacion[]> {
  const { data } = await api.get<Evaluacion[]>('/api/v1/estructura/evaluaciones', { params: filters });
  return data;
}

export async function crearEvaluacion(payload: Partial<Evaluacion>): Promise<Evaluacion> {
  const { data } = await api.post<Evaluacion>('/api/v1/estructura/evaluaciones', payload);
  return data;
}

export async function actualizarEvaluacion(id: string, payload: Partial<Evaluacion>): Promise<Evaluacion> {
  const { data } = await api.put<Evaluacion>(`/api/v1/estructura/evaluaciones/${id}`, payload);
  return data;
}
