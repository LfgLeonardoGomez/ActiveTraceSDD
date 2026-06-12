import api from '@/shared/services/api';
import type {
  Equipo,
  UsuarioDocente,
  Asignacion,
  AsignacionRequest,
  AsignacionMasivaRequest,
  ClonarEquipoRequest,
} from '../types/equipos.types';

export async function getMisEquipos(filters?: Record<string, string>): Promise<Equipo[]> {
  const { data } = await api.get<Equipo[]>('/api/v1/equipos/mis-equipos', { params: filters });
  return data;
}

export async function getUsuarios(): Promise<UsuarioDocente[]> {
  const { data } = await api.get<UsuarioDocente[]>('/api/v1/equipos/usuarios');
  return data;
}

export async function crearUsuario(payload: Partial<UsuarioDocente>): Promise<UsuarioDocente> {
  const { data } = await api.post<UsuarioDocente>('/api/v1/equipos/usuarios', payload);
  return data;
}

export async function actualizarUsuario(id: string, payload: Partial<UsuarioDocente>): Promise<UsuarioDocente> {
  const { data } = await api.put<UsuarioDocente>(`/api/v1/equipos/usuarios/${id}`, payload);
  return data;
}

export async function getAsignaciones(filters?: Record<string, string>): Promise<Asignacion[]> {
  const { data } = await api.get<Asignacion[]>('/api/v1/equipos/asignaciones', { params: filters });
  return data;
}

export async function crearAsignacion(payload: AsignacionRequest): Promise<Asignacion> {
  const { data } = await api.post<Asignacion>('/api/v1/equipos/asignaciones', payload);
  return data;
}

export async function asignacionMasiva(
  payload: AsignacionMasivaRequest,
): Promise<{ count: number; errors?: unknown[] }> {
  const { data } = await api.post<{ count: number; errors?: unknown[] }>(
    '/api/v1/equipos/asignaciones/masiva',
    payload,
  );
  return data;
}

export async function clonarEquipo(payload: ClonarEquipoRequest): Promise<{ asignaciones_creadas: number }> {
  const { data } = await api.post<{ asignaciones_creadas: number }>('/api/v1/equipos/clonar', payload);
  return data;
}

export async function actualizarVigencia(
  payload: Record<string, string>,
): Promise<{ updated_count: number }> {
  const { data } = await api.put<{ updated_count: number }>('/api/v1/equipos/vigencia', payload);
  return data;
}

export function getExportUrl(equipoId: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? '';
  return `${base}/api/v1/equipos/export?equipo_id=${equipoId}`;
}
