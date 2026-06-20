import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type { MetricasColoquios, Convocatoria, ImportResult, Reserva } from '../types/coloquios.types';

// Raw shape returned by GET /api/coloquios/ (EvaluacionResponseSchema)
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

// Raw shape returned by GET /api/coloquios/reservas-activas (ReservaResponseSchema)
interface ReservaApiItem {
  id: string;
  evaluacion_id: string;
  alumno_id: string;
  alumno_nombre: string;
  fecha_hora: string;
  estado: string;
  created_at: string;
}

function mapEvaluacionApiToConvocatoria(item: EvaluacionApiItem): Convocatoria {
  return {
    id: item.id,
    materia: item.materia_id,
    materia_id: item.materia_id,
    instancia: parseInt(item.instancia, 10) || 1,
    titulo: item.instancia,
    cohorte: item.cohorte_id,
    cohorte_id: item.cohorte_id,
    dias: [],
    estado: 'activa',
    total_convocados: item.convocados,
    reservas_activas: item.reservas_activas,
    cupos_libres: item.cupos_libres_por_dia,
  };
}

function mapReservaApiToView(item: ReservaApiItem): Reserva {
  return {
    id: item.id,
    alumno: item.alumno_nombre,
    alumno_id: item.alumno_id,
    convocatoria_id: item.evaluacion_id,
    dia: item.fecha_hora,
    horario: item.fecha_hora,
    estado: item.estado,
  };
}

export async function getMetricas(): Promise<MetricasColoquios> {
  const { data } = await api.get<MetricasColoquios>('/api/coloquios/metricas');
  return data;
}

export async function getConvocatorias(filters?: Record<string, string>): Promise<Convocatoria[]> {
  const { data } = await api.get<EvaluacionApiItem[] | Paginated<EvaluacionApiItem>>('/api/coloquios/', { params: filters });
  return toList(data).map(mapEvaluacionApiToConvocatoria);
}

export async function crearConvocatoria(payload: Partial<Convocatoria>): Promise<Convocatoria> {
  const { data } = await api.post<EvaluacionApiItem>('/api/coloquios/', payload);
  return mapEvaluacionApiToConvocatoria(data);
}

export async function getConvocatoriaDetail(id: string): Promise<Convocatoria> {
  const { data } = await api.get<EvaluacionApiItem>(`/api/coloquios/${id}`);
  return mapEvaluacionApiToConvocatoria(data);
}

export async function importarAlumnos(formData: FormData): Promise<ImportResult> {
  const { data } = await api.post<ImportResult>('/api/coloquios/importar-alumnos', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function getAdminConvocatorias(): Promise<Convocatoria[]> {
  const { data } = await api.get<EvaluacionApiItem[] | Paginated<EvaluacionApiItem>>('/api/coloquios/admin');
  return toList(data).map(mapEvaluacionApiToConvocatoria);
}

export async function cerrarConvocatoria(id: string): Promise<Convocatoria> {
  const { data } = await api.put<EvaluacionApiItem>(`/api/coloquios/admin/${id}`);
  return mapEvaluacionApiToConvocatoria(data);
}

export async function getReservasActivas(): Promise<Reserva[]> {
  const { data } = await api.get<ReservaApiItem[] | Paginated<ReservaApiItem>>('/api/coloquios/reservas-activas');
  return toList(data).map(mapReservaApiToView);
}
