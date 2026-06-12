import api from '@/shared/services/api';
import type { Tarea, TareaFilters } from '../types/tareas.types';

export async function getMisTareas(filters?: TareaFilters): Promise<Tarea[]> {
  const { data } = await api.get<Tarea[]>('/api/v1/tareas/mis-tareas', { params: filters });
  return data;
}

export async function getTareasAdmin(filters?: TareaFilters): Promise<Tarea[]> {
  const { data } = await api.get<Tarea[]>('/api/v1/tareas', { params: filters });
  return data;
}

export async function asignarTarea(payload: Partial<Tarea>): Promise<Tarea> {
  const { data } = await api.post<Tarea>('/api/v1/tareas', payload);
  return data;
}

export async function actualizarEstadoTarea(id: string, payload: { estado: string; comentario?: string }): Promise<Tarea> {
  const { data } = await api.put<Tarea>(`/api/v1/tareas/${id}`, payload);
  return data;
}
