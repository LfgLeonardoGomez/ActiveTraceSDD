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

// ---------------------------------------------------------------------------
// Raw API shapes
// ---------------------------------------------------------------------------

// GET /api/auditoria/panel/acciones-por-dia → AccionesPorDiaResponse
// items: AccionesPorDiaItem { fecha: date, total: int }
interface AccionesPorDiaApiItem {
  fecha: string;
  total: number;
}
interface AccionesPorDiaApiResponse {
  items: AccionesPorDiaApiItem[];
  rango: { desde: string; hasta: string };
}

// GET /api/auditoria/panel/comunicaciones-por-docente → ComunicacionesPorDocenteResponse
// items: ComunicacionesPorDocenteItem { usuario_id, usuario_nombre, conteos: { Pendiente, Enviando, Enviado, Error, Cancelado } }
interface ComunicacionesPorDocenteApiItem {
  usuario_id: string;
  usuario_nombre: string;
  conteos: {
    Pendiente?: number;
    Enviando?: number;
    Enviado?: number;
    Error?: number;
    Cancelado?: number;
  };
}
interface ComunicacionesPorDocenteApiResponse {
  items: ComunicacionesPorDocenteApiItem[];
}

// GET /api/auditoria/panel/interacciones-por-docente-materia → InteraccionesPorDocenteMateriaResponse
// items: InteraccionesPorDocenteMateriaItem { actor_id, actor_nombre, materia_id, materia_nombre, accion, categoria, total }
interface InteraccionesPorDocenteMateriaApiItem {
  actor_id: string;
  actor_nombre: string;
  materia_id: string | null;
  materia_nombre: string | null;
  accion: string;
  categoria: string;
  total: number;
}
interface InteraccionesPorDocenteMateriaApiResponse {
  items: InteraccionesPorDocenteMateriaApiItem[];
}

// GET /api/auditoria/panel/ultimas-acciones → UltimasAccionesResponse
// items: UltimaAccionItem { id, fecha_hora, actor_id, impersonado_id, materia_id, accion, categoria, filas_afectadas, ip, user_agent }
interface UltimaAccionApiItem {
  id: string;
  fecha_hora: string;
  actor_id: string;
  impersonado_id: string | null;
  materia_id: string | null;
  accion: string;
  categoria: string;
  filas_afectadas: number;
  ip: string | null;
  user_agent: string | null;
}
interface UltimasAccionesApiResponse {
  items: UltimaAccionApiItem[];
}

// GET /api/auditoria/log → AuditLogPageResponse
// items: AuditLogEntrySchema { id, fecha_hora, actor_id, impersonado_id, materia_id, accion, categoria, filas_afectadas, ip, user_agent, detalle }
interface AuditLogApiItem {
  id: string;
  fecha_hora: string;
  actor_id: string;
  impersonado_id: string | null;
  materia_id: string | null;
  accion: string;
  categoria: string;
  filas_afectadas: number;
  ip: string | null;
  user_agent: string | null;
  detalle: Record<string, unknown> | null;
}
interface AuditLogApiResponse {
  items: AuditLogApiItem[];
  total: number;
  page: number;
  pages: number;
}

// GET /api/auditoria/catalogo-acciones → CatalogoAccionesResponse
// items: CatalogoAccionItem { codigo, categoria }
interface CatalogoAccionApiItem {
  codigo: string;
  categoria: string;
}
interface CatalogoAccionesApiResponse {
  items: CatalogoAccionApiItem[];
}

// ---------------------------------------------------------------------------
// Mapping functions
// ---------------------------------------------------------------------------

function mapAccionPorDia(item: AccionesPorDiaApiItem): AccionPorDia {
  // View model expects { fecha, cantidad } — API returns { fecha, total }
  return { fecha: item.fecha, cantidad: item.total };
}

function mapComunicacionPorDocente(item: ComunicacionesPorDocenteApiItem): ComunicacionPorDocente {
  // View model expects { docente_id, docente_nombre, enviadas, pendientes, fallidas }
  return {
    docente_id: item.usuario_id,
    docente_nombre: item.usuario_nombre,
    enviadas: item.conteos.Enviado ?? 0,
    pendientes: item.conteos.Pendiente ?? 0,
    fallidas: item.conteos.Error ?? 0,
  };
}

function mapInteraccionPorDocenteMateria(item: InteraccionesPorDocenteMateriaApiItem): InteraccionPorDocenteMateria {
  // View model expects { docente_id, docente_nombre, materia_id, materia_nombre, interacciones }
  return {
    docente_id: item.actor_id,
    docente_nombre: item.actor_nombre,
    materia_id: item.materia_id ?? '',
    materia_nombre: item.materia_nombre ?? '',
    interacciones: item.total,
  };
}

function mapUltimaAccion(item: UltimaAccionApiItem): UltimaAccion {
  // View model expects { id, timestamp, usuario_nombre, accion, modulo, descripcion }
  return {
    id: item.id,
    timestamp: item.fecha_hora,
    usuario_nombre: item.actor_id,
    accion: item.accion,
    modulo: item.categoria,
    descripcion: item.accion,
  };
}

function mapAuditLogEntry(item: AuditLogApiItem): AuditLogEntry {
  // View model expects { id, timestamp, usuario_id, usuario_nombre, accion, modulo, descripcion, materia_id?, materia_nombre?, estado }
  return {
    id: item.id,
    timestamp: item.fecha_hora,
    usuario_id: item.actor_id,
    usuario_nombre: item.actor_id,
    accion: item.accion,
    modulo: item.categoria,
    descripcion: item.accion,
    materia_id: item.materia_id ?? undefined,
    materia_nombre: undefined,
    estado: 'ok',
  };
}

function mapCatalogoAccion(item: CatalogoAccionApiItem): CatalogoAccion {
  // View model expects { codigo, descripcion } — API returns { codigo, categoria }
  return { codigo: item.codigo, descripcion: item.categoria };
}

// ---------------------------------------------------------------------------
// Service functions
// ---------------------------------------------------------------------------

export async function getAccionesPorDia(): Promise<AccionPorDia[]> {
  const { data } = await api.get<AccionesPorDiaApiResponse>('/api/auditoria/panel/acciones-por-dia');
  return data.items.map(mapAccionPorDia);
}

export async function getComunicacionesPorDocente(): Promise<ComunicacionPorDocente[]> {
  const { data } = await api.get<ComunicacionesPorDocenteApiResponse>('/api/auditoria/panel/comunicaciones-por-docente');
  return data.items.map(mapComunicacionPorDocente);
}

export async function getInteraccionesPorDocenteMateria(): Promise<InteraccionPorDocenteMateria[]> {
  const { data } = await api.get<InteraccionesPorDocenteMateriaApiResponse>('/api/auditoria/panel/interacciones-por-docente-materia');
  return data.items.map(mapInteraccionPorDocenteMateria);
}

export async function getUltimasAcciones(): Promise<UltimaAccion[]> {
  const { data } = await api.get<UltimasAccionesApiResponse>('/api/auditoria/panel/ultimas-acciones');
  return data.items.map(mapUltimaAccion);
}

export async function getAuditLog(filters?: AuditLogFilters): Promise<{ items: AuditLogEntry[]; total: number }> {
  const { data } = await api.get<AuditLogApiResponse>('/api/auditoria/log', { params: filters });
  return { items: data.items.map(mapAuditLogEntry), total: data.total };
}

export async function getCatalogoAcciones(): Promise<CatalogoAccion[]> {
  const { data } = await api.get<CatalogoAccionesApiResponse>('/api/auditoria/catalogo-acciones');
  return data.items.map(mapCatalogoAccion);
}
