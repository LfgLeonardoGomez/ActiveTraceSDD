import api from '@/shared/services/api';
import type {
  AccionPorDia,
  ComunicacionPorDocente,
  InteraccionPorDocenteMateria,
  AuditLogEntry,
  UltimaAccion,
  CatalogoAccion,
  AuditLogFilters,
} from '../types/auditoria.types';

export async function getAccionesPorDia(): Promise<AccionPorDia[]> {
  const { data } = await api.get<AccionPorDia[]>('/api/auditoria/panel/acciones-por-dia');
  return data;
}

export async function getComunicacionesPorDocente(): Promise<ComunicacionPorDocente[]> {
  const { data } = await api.get<ComunicacionPorDocente[]>('/api/auditoria/panel/comunicaciones-por-docente');
  return data;
}

export async function getInteraccionesPorDocenteMateria(): Promise<InteraccionPorDocenteMateria[]> {
  const { data } = await api.get<InteraccionPorDocenteMateria[]>('/api/auditoria/panel/interacciones-por-docente-materia');
  return data;
}

export async function getUltimasAcciones(): Promise<UltimaAccion[]> {
  const { data } = await api.get<UltimaAccion[]>('/api/auditoria/panel/ultimas-acciones');
  return data;
}

export async function getAuditLog(filters?: AuditLogFilters): Promise<{ items: AuditLogEntry[]; total: number }> {
  const { data } = await api.get('/api/auditoria/log', { params: filters });
  return data;
}

export async function getCatalogoAcciones(): Promise<CatalogoAccion[]> {
  const { data } = await api.get<CatalogoAccion[]>('/api/auditoria/catalogo-acciones');
  return data;
}
