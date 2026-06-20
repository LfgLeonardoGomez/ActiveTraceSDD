import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type { Carrera, Cohorte, Programa, Evaluacion } from '../types/estructura.types';

// ---------------------------------------------------------------------------
// Raw API shapes (backend schemas/estructura.py)
// ---------------------------------------------------------------------------

// CarreraRead: { id, tenant_id, codigo, nombre, estado, created_at?, updated_at?, deleted_at? }
interface CarreraApiItem {
  id: string;
  tenant_id: string;
  codigo: string;
  nombre: string;
  estado: string;
  created_at: string | null;
  updated_at: string | null;
  deleted_at?: string | null;
}

// CohorteRead: { id, tenant_id, carrera_id, nombre, anio, vig_desde, vig_hasta?, estado, created_at? }
// View model (coordinacion) expects: { id, nombre, year, fecha_desde, fecha_hasta, estado }
interface CohorteApiItem {
  id: string;
  tenant_id: string;
  carrera_id: string;
  nombre: string;
  anio: number;
  vig_desde: string;
  vig_hasta: string | null;
  estado: string;
  created_at: string | null;
  updated_at: string | null;
  deleted_at?: string | null;
}

// EvaluacionResponseSchema: { id, materia_id, cohorte_id, tipo, instancia, dias_disponibles, cupo_por_dia, convocados, reservas_activas, cupos_libres_por_dia, created_at }
interface EvaluacionApiItem {
  id: string;
  materia_id: string;
  cohorte_id: string;
  tipo: string;
  instancia: string;
  dias_disponibles: number;
  cupo_por_dia: number;
  convocados: number;
  reservas_activas: number;
  cupos_libres_por_dia: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Mapping functions
// ---------------------------------------------------------------------------

function mapCarreraApiToView(item: CarreraApiItem): Carrera {
  return {
    id: item.id,
    codigo: item.codigo,
    nombre: item.nombre,
    activa: item.estado.toLowerCase().startsWith('activ'),
    creada: item.created_at ?? '',
  };
}

function mapCohorteApiToView(item: CohorteApiItem): Cohorte {
  return {
    id: item.id,
    nombre: item.nombre,
    year: item.anio,
    fecha_desde: item.vig_desde,
    fecha_hasta: item.vig_hasta ?? '',
    estado: item.estado,
  };
}

function mapEvaluacionApiToView(item: EvaluacionApiItem): Evaluacion {
  return {
    id: item.id,
    materia: item.materia_id,
    materia_id: item.materia_id,
    cohorte: item.cohorte_id,
    cohorte_id: item.cohorte_id,
    tipo: item.tipo as Evaluacion['tipo'],
    instancia: parseInt(item.instancia, 10) || 1,
    fecha: item.created_at,
    titulo: item.instancia,
  };
}

// ---------------------------------------------------------------------------
// Service functions
// ---------------------------------------------------------------------------

// Carreras / Cohortes live in the estructura router mounted under /api/v1/admin.
export async function getCarreras(): Promise<Carrera[]> {
  const { data } = await api.get<CarreraApiItem[] | Paginated<CarreraApiItem>>('/api/v1/admin/carreras');
  return toList(data).map(mapCarreraApiToView);
}

export async function crearCarrera(payload: Partial<Carrera>): Promise<Carrera> {
  const { data } = await api.post<CarreraApiItem>('/api/v1/admin/carreras', payload);
  return mapCarreraApiToView(data);
}

export async function actualizarCarrera(id: string, payload: Partial<Carrera>): Promise<Carrera> {
  const { data } = await api.put<CarreraApiItem>(`/api/v1/admin/carreras/${id}`, payload);
  return mapCarreraApiToView(data);
}

export async function getCohortes(filters?: Record<string, string>): Promise<Cohorte[]> {
  const { data } = await api.get<CohorteApiItem[] | Paginated<CohorteApiItem>>('/api/v1/admin/cohortes', { params: filters });
  return toList(data).map(mapCohorteApiToView);
}

export async function crearCohorte(payload: Partial<Cohorte>): Promise<Cohorte> {
  const { data } = await api.post<CohorteApiItem>('/api/v1/admin/cohortes', payload);
  return mapCohorteApiToView(data);
}

export async function actualizarCohorte(id: string, payload: Partial<Cohorte>): Promise<Cohorte> {
  const { data } = await api.put<CohorteApiItem>(`/api/v1/admin/cohortes/${id}`, payload);
  return mapCohorteApiToView(data);
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
  const { data } = await api.get<EvaluacionApiItem[] | Paginated<EvaluacionApiItem>>('/api/coloquios/', { params: filters });
  return toList(data).map(mapEvaluacionApiToView);
}

export async function crearEvaluacion(payload: Partial<Evaluacion>): Promise<Evaluacion> {
  const { data } = await api.post<EvaluacionApiItem>('/api/coloquios/', payload);
  return mapEvaluacionApiToView(data);
}

export async function actualizarEvaluacion(id: string, payload: Partial<Evaluacion>): Promise<Evaluacion> {
  const { data } = await api.patch<EvaluacionApiItem>(`/api/coloquios/${id}`, payload);
  return mapEvaluacionApiToView(data);
}
