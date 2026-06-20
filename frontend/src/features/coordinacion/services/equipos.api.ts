import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type {
  Equipo,
  UsuarioDocente,
  Asignacion,
  AsignacionRequest,
  AsignacionMasivaRequest,
  ClonarEquipoRequest,
} from '../types/equipos.types';

// Raw shape returned by GET /api/v1/equipos/mis-equipos (EquipoRead — per-assignment row with denormalised names).
interface MisEquiposApiItem {
  id: string;
  rol: string | null;
  desde: string | null;
  hasta: string | null;
  materia_id: string | null;
  carrera_id: string | null;
  cohorte_id: string | null;
  estado_vigencia: string | null;
  materia_nombre: string | null;
  carrera_nombre: string | null;
  cohorte_nombre: string | null;
  usuario_nombre: string | null;
  usuario_apellidos: string | null;
}

// Raw shape returned by GET /api/v1/asignaciones (AsignacionRead)
interface AsignacionApiItem {
  id: string;
  tenant_id: string;
  usuario_id: string;
  rol: string;
  desde: string;
  hasta: string | null;
  materia_id: string | null;
  carrera_id: string | null;
  cohorte_id: string | null;
  comisiones: string[] | null;
  responsable_id: string | null;
  estado_vigencia: string;
}

// Raw shape returned by GET /api/v1/admin/usuarios (UsuarioListRead — used as a stand-in for docentes)
interface UsuarioDocenteApiItem {
  id: string;
  tenant_id: string;
  nombre: string;
  apellidos: string;
  email: string;
  estado: string;
  legajo: string | null;
  regional: string | null;
}

function mapAsignacionApiToView(item: AsignacionApiItem): Asignacion {
  return {
    id: item.id,
    docente: item.usuario_id,
    docente_id: item.usuario_id,
    materia: item.materia_id ?? '—',
    materia_id: item.materia_id ?? '',
    carrera: item.carrera_id ?? '—',
    cohorte: item.cohorte_id ?? '—',
    cohorte_id: item.cohorte_id ?? '',
    rol: item.rol,
    fecha_desde: item.desde,
    fecha_hasta: item.hasta ?? '—',
    estado: item.estado_vigencia,
  };
}

export async function getMisEquipos(filters?: Record<string, string>): Promise<Equipo[]> {
  const { data } = await api.get<MisEquiposApiItem[] | Paginated<MisEquiposApiItem>>(
    '/api/v1/equipos/mis-equipos',
    { params: filters },
  );
  return toList(data).map((item) => ({
    id: item.id,
    materia: item.materia_nombre ?? '—',
    materia_id: item.materia_id ?? '',
    carrera: item.carrera_nombre ?? '—',
    cohorte: item.cohorte_nombre ?? '—',
    cohorte_id: item.cohorte_id ?? '',
    roles: item.rol ? [item.rol] : [],
    vigencia_desde: item.desde ?? '—',
    vigencia_hasta: item.hasta ?? '—',
    estado: item.estado_vigencia ?? '—',
  }));
}

export async function getUsuarios(): Promise<UsuarioDocente[]> {
  const { data } = await api.get<UsuarioDocenteApiItem[] | Paginated<UsuarioDocenteApiItem>>(
    '/api/v1/admin/usuarios',
  );
  return toList(data).map((item) => ({
    id: item.id,
    nombre: `${item.nombre} ${item.apellidos}`.trim(),
    email: item.email,
    rol: '',
    regional: item.regional ?? '',
    activo: item.estado.toLowerCase().startsWith('activ'),
  }));
}

export async function crearUsuario(payload: Partial<UsuarioDocente>): Promise<UsuarioDocente> {
  const { data } = await api.post<UsuarioDocenteApiItem>('/api/v1/admin/usuarios', payload);
  return {
    id: data.id,
    nombre: `${data.nombre} ${data.apellidos}`.trim(),
    email: data.email,
    rol: '',
    regional: data.regional ?? '',
    activo: data.estado.toLowerCase().startsWith('activ'),
  };
}

export async function actualizarUsuario(id: string, payload: Partial<UsuarioDocente>): Promise<UsuarioDocente> {
  const { data } = await api.put<UsuarioDocenteApiItem>(`/api/v1/admin/usuarios/${id}`, payload);
  return {
    id: data.id,
    nombre: `${data.nombre} ${data.apellidos}`.trim(),
    email: data.email,
    rol: '',
    regional: data.regional ?? '',
    activo: data.estado.toLowerCase().startsWith('activ'),
  };
}

export async function getAsignaciones(filters?: Record<string, string>): Promise<Asignacion[]> {
  const { data } = await api.get<AsignacionApiItem[] | Paginated<AsignacionApiItem>>(
    '/api/v1/asignaciones',
    { params: filters },
  );
  return toList(data).map(mapAsignacionApiToView);
}

export async function crearAsignacion(payload: AsignacionRequest): Promise<Asignacion> {
  const { data } = await api.post<AsignacionApiItem>('/api/v1/asignaciones', payload);
  return mapAsignacionApiToView(data);
}

export async function asignacionMasiva(
  payload: AsignacionMasivaRequest,
): Promise<{ count: number; errors?: unknown[] }> {
  const { data } = await api.post<{ count: number; errors?: unknown[] }>(
    '/api/v1/equipos/asignacion-masiva',
    payload,
  );
  return data;
}

export async function clonarEquipo(payload: ClonarEquipoRequest): Promise<{ asignaciones_creadas: number }> {
  const { data } = await api.post<{ preview_count: number; created_count?: number }>('/api/v1/equipos/clonar', payload);
  return { asignaciones_creadas: data.created_count ?? data.preview_count };
}

export async function actualizarVigencia(
  payload: Record<string, string>,
): Promise<{ updated_count: number }> {
  const { materia_id, carrera_id, cohorte_id, ...body } = payload;
  const { data } = await api.put<{ count: number }>(
    `/api/v1/equipos/${materia_id}/${carrera_id}/${cohorte_id}/vigencia`,
    body,
  );
  return { updated_count: data.count };
}

export function getExportUrl(equipoId: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? '';
  return `${base}/api/v1/equipos/exportar?equipo_id=${equipoId}`;
}
