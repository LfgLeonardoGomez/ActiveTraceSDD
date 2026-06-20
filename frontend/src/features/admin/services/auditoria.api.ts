import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
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
  const { data } = await api.get<AccionPorDia[] | Paginated<AccionPorDia>>('/api/auditoria/panel/acciones-por-dia');
  return toList(data);
}

export async function getComunicacionesPorDocente(): Promise<ComunicacionPorDocente[]> {
  const { data } = await api.get<ComunicacionPorDocente[] | Paginated<ComunicacionPorDocente>>('/api/auditoria/panel/comunicaciones-por-docente');
  return toList(data);
}

export async function getInteraccionesPorDocenteMateria(): Promise<InteraccionPorDocenteMateria[]> {
  const { data } = await api.get<InteraccionPorDocenteMateria[] | Paginated<InteraccionPorDocenteMateria>>('/api/auditoria/panel/interacciones-por-docente-materia');
  return toList(data);
}

export async function getUltimasAcciones(): Promise<UltimaAccion[]> {
  const { data } = await api.get<UltimaAccion[] | Paginated<UltimaAccion>>('/api/auditoria/panel/ultimas-acciones');
  return toList(data);
}

export async function getAuditLog(filters?: AuditLogFilters): Promise<{ items: AuditLogEntry[]; total: number }> {
  const { data } = await api.get('/api/auditoria/log', { params: filters });
  return data;
}

export async function getCatalogoAcciones(): Promise<CatalogoAccion[]> {
  const { data } = await api.get<CatalogoAccion[] | Paginated<CatalogoAccion>>('/api/auditoria/catalogo-acciones');
  return toList(data);
}
