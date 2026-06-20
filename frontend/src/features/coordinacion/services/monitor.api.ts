import api from '@/shared/services/api';
import type {
  MonitorFilters,
  MonitorEntry,
  AuditoriaEntry,
  PaginatedResponse,
} from '../types/monitor.types';

// Raw shape returned by GET /api/analisis/monitor/general (MonitorItemSchema)
interface MonitorApiItem {
  entrada_padron_id: string;
  alumno_nombre: string;
  email: string;
  materia_id: string;
  materia_nombre: string;
  actividades_aprobadas: number;
  actividades_totales: number;
  estado: string;
}

interface MonitorApiResponse {
  items: MonitorApiItem[];
  total: number;
  page: number;
  pages: number;
}

// Raw shape returned by GET /api/auditoria/log (AuditLogEntrySchema)
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

function mapMonitorApiToView(item: MonitorApiItem): MonitorEntry {
  return {
    alumno_id: item.entrada_padron_id,
    nombre: item.alumno_nombre,
    email: item.email,
    comision: '',
    regional: '',
    materia: item.materia_nombre,
    actividad: `${item.actividades_aprobadas}/${item.actividades_totales}`,
    estado: item.estado,
    ultima_actividad: null,
  };
}

function mapAuditLogApiToView(item: AuditLogApiItem): AuditoriaEntry {
  return {
    id: item.id,
    fecha_hora: item.fecha_hora,
    docente: item.actor_id,
    rol: '',
    accion: item.accion,
    materia: item.materia_id,
    registros_afectados: item.filas_afectadas,
    ip: item.ip ?? '',
    user_agent: item.user_agent ?? '',
    detalle: {
      request_payload: null,
      response_status: null,
      duration: null,
      full_user_agent: item.user_agent,
    },
  };
}

export async function getMonitorGeneral(
  filters?: MonitorFilters,
  page = 1,
): Promise<PaginatedResponse<MonitorEntry>> {
  const { data } = await api.get<MonitorApiResponse>('/api/analisis/monitor/general', {
    params: { ...filters, page },
  });
  return {
    data: data.items.map(mapMonitorApiToView),
    total: data.total,
    page: data.page,
    total_pages: data.pages,
  };
}

export async function getAuditoria(
  filters?: MonitorFilters,
  page = 1,
): Promise<PaginatedResponse<AuditoriaEntry>> {
  const { data } = await api.get<AuditLogApiResponse>('/api/auditoria/log', {
    params: { ...filters, page },
  });
  return {
    data: data.items.map(mapAuditLogApiToView),
    total: data.total,
    page: data.page,
    total_pages: data.pages,
  };
}
