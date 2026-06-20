import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type { Tarea, TareaFilters } from '../types/tareas.types';

export async function getMisTareas(filters?: TareaFilters): Promise<Tarea[]> {
  const { data } = await api.get<Tarea[] | Paginated<Tarea>>('/api/tareas/mis-tareas', { params: filters });
  return toList(data);
}

export async function getTareasAdmin(filters?: TareaFilters): Promise<Tarea[]> {
  const { data } = await api.get<Tarea[] | Paginated<Tarea>>('/api/tareas/', { params: filters });
  return toList(data);
}

export async function asignarTarea(payload: Partial<Tarea>): Promise<Tarea> {
  const { data } = await api.post<Tarea>('/api/tareas/', payload);
  return data;
}

export async function actualizarEstadoTarea(id: string, payload: { estado: string; comentario?: string }): Promise<Tarea> {
  const { data } = await api.put<Tarea>(`/api/tareas/${id}/estado`, payload);
  return data;
}
