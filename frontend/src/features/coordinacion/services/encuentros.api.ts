import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type { Encuentro, SerieRecurrenteRequest, Guardia } from '../types/encuentros.types';

// Raw shape returned by GET /api/v1/encuentros/instancias (InstanciaRead)
interface InstanciaApiItem {
  id: string;
  tenant_id: string;
  slot_id: string | null;
  materia_id: string;
  titulo: string | null;
  fecha: string;
  hora: string;
  estado: string;
  meet_url: string | null;
  video_url: string | null;
  comentario: string | null;
  created_at: string | null;
  updated_at: string | null;
}

// Raw shape returned by GET /api/v1/guardias (GuardiaRead)
interface GuardiaApiItem {
  id: string;
  tenant_id: string;
  tutor_id: string;
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
  fecha: string;
  horario: string | null;
  descripcion: string;
  estado: string;
  comentarios: string | null;
  created_at: string | null;
  updated_at: string | null;
}

function mapInstanciaApiToEncuentro(item: InstanciaApiItem): Encuentro {
  return {
    id: item.id,
    materia: item.materia_id,
    materia_id: item.materia_id,
    cohorte: '',
    cohorte_id: '',
    docente: '',
    docente_id: '',
    fecha: item.fecha,
    hora: item.hora,
    titulo: item.titulo ?? undefined,
    estado: item.estado as Encuentro['estado'],
    enlace: item.meet_url,
    grabacion: item.video_url,
    comentario_interno: item.comentario,
  };
}

function mapGuardiaApiToView(item: GuardiaApiItem): Guardia {
  // The API returns a single `horario` string (e.g. "10:00-11:00").
  // The view model expects separate horario_desde / horario_hasta.
  const [horario_desde = '', horario_hasta = ''] = (item.horario ?? '').split('-');
  return {
    id: item.id,
    tutor: item.tutor_id,
    tutor_id: item.tutor_id,
    materia: item.materia_id,
    materia_id: item.materia_id,
    carrera: item.carrera_id,
    cohorte: item.cohorte_id,
    dia: item.fecha,
    horario_desde: horario_desde.trim(),
    horario_hasta: horario_hasta.trim(),
    estado: item.estado,
    comentarios: item.comentarios,
  };
}

export async function getEncuentros(filters?: Record<string, string>): Promise<Encuentro[]> {
  const { data } = await api.get<InstanciaApiItem[] | Paginated<InstanciaApiItem>>('/api/v1/encuentros/instancias', { params: filters });
  return toList(data).map(mapInstanciaApiToEncuentro);
}

export async function crearEncuentro(payload: Partial<Encuentro>): Promise<Encuentro> {
  const { data } = await api.post<InstanciaApiItem>('/api/v1/encuentros/instancias', payload);
  return mapInstanciaApiToEncuentro(data);
}

export async function crearRecurrente(
  payload: SerieRecurrenteRequest,
): Promise<{ instancias: Encuentro[]; count: number }> {
  const { data } = await api.post<{ instancias: InstanciaApiItem[]; count: number }>(
    '/api/v1/encuentros/recurrente',
    payload,
  );
  return {
    instancias: data.instancias.map(mapInstanciaApiToEncuentro),
    count: data.count,
  };
}

export async function editarEncuentro(id: string, payload: Partial<Encuentro>): Promise<Encuentro> {
  const { data } = await api.put<InstanciaApiItem>(`/api/v1/encuentros/instancias/${id}`, payload);
  return mapInstanciaApiToEncuentro(data);
}

export async function getContenidoAula(filters?: Record<string, string>): Promise<unknown> {
  const { data } = await api.get('/api/v1/encuentros/bloque-html', { params: filters });
  return data;
}

export async function getGuardias(filters?: Record<string, string>): Promise<Guardia[]> {
  const { data } = await api.get<GuardiaApiItem[] | Paginated<GuardiaApiItem>>('/api/v1/guardias', { params: filters });
  return toList(data).map(mapGuardiaApiToView);
}

export async function registrarGuardia(payload: Partial<Guardia>): Promise<Guardia> {
  const { data } = await api.post<GuardiaApiItem>('/api/v1/guardias', payload);
  return mapGuardiaApiToView(data);
}
