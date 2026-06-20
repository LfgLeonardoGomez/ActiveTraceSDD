import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type { Tarea, TareaFilters } from '../types/tareas.types';

// Raw shape returned by GET /api/tareas/ (TareaResponseSchema)
interface TareaApiItem {
  id: string;
  tenant_id: string;
  titulo: string;
  descripcion: string | null;
  criterio_cierre: string | null;
  estado: string;
  aprobada: boolean;
  devuelta: boolean;
  asignado_a: string;
  asignado_por: string;
  revisada_por: string | null;
  revisada_at: string | null;
  materia_id: string | null;
  contexto_id: string | null;
  created_at: string;
  updated_at: string;
}

function mapTareaApiToView(item: TareaApiItem): Tarea {
  return {
    id: item.id,
    titulo: item.titulo,
    descripcion: item.descripcion ?? '',
    asignado: item.asignado_a,
    asignado_id: item.asignado_a,
    asignador: item.asignado_por,
    asignador_id: item.asignado_por,
    materia: item.materia_id,
    estado: item.estado as Tarea['estado'],
    prioridad: 'normal',
    fecha_creacion: item.created_at,
    fecha_limite: null,
    comentarios: [],
  };
}

export async function getMisTareas(filters?: TareaFilters): Promise<Tarea[]> {
  const { data } = await api.get<TareaApiItem[] | Paginated<TareaApiItem>>('/api/tareas/mis-tareas', { params: filters });
  return toList(data).map(mapTareaApiToView);
}

export async function getTareasAdmin(filters?: TareaFilters): Promise<Tarea[]> {
  const { data } = await api.get<TareaApiItem[] | Paginated<TareaApiItem>>('/api/tareas/', { params: filters });
  return toList(data).map(mapTareaApiToView);
}

export async function asignarTarea(payload: Partial<Tarea>): Promise<Tarea> {
  const { data } = await api.post<TareaApiItem>('/api/tareas/', payload);
  return mapTareaApiToView(data);
}

export async function actualizarEstadoTarea(id: string, payload: { estado: string; comentario?: string }): Promise<Tarea> {
  const { data } = await api.put<TareaApiItem>(`/api/tareas/${id}/estado`, payload);
  return mapTareaApiToView(data);
}
