export interface MonitorFilters {
  nombre?: string;
  email?: string;
  comision?: string;
  regional?: string;
  materia?: string;
  actividad?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  q?: string;
  docente?: string;
  tipo_accion?: string;
}

export interface MonitorEntry {
  alumno_id: string;
  nombre: string;
  email: string;
  comision: string;
  regional: string;
  materia: string;
  actividad: string;
  estado: string;
  ultima_actividad: string | null;
}

export interface AuditoriaDetail {
  request_payload: string | null;
  response_status: number | null;
  duration: number | null;
  full_user_agent: string | null;
}

export interface AuditoriaEntry {
  id: string;
  fecha_hora: string;
  docente: string;
  rol: string;
  accion: string;
  materia: string | null;
  registros_afectados: number;
  ip: string;
  user_agent: string;
  detalle: AuditoriaDetail;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  total_pages: number;
}
