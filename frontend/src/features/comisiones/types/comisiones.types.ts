// ── Commission ──
export interface MateriaCohorte {
  id: string;
  materia_id: string;
  materia_nombre: string;
  cohorte_nombre: string;
}

// ── Grade Import ──
export interface ActivityDTO {
  id: string;
  nombre: string;
  tipo: string;
  fecha: string;
  filas_detectadas: number;
}

export interface AlumnoPreviewDTO {
  legajo: string;
  nombre: string;
  email: string;
  notas_detectadas: number;
}

export interface ImportPreviewResponse {
  actividades: ActivityDTO[];
  alumnos: AlumnoPreviewDTO[];
}

export interface ImportConfirmRequest {
  materia_id: string;
  activities_selected: string[];
}

export interface ImportError {
  row: number;
  legajo?: string;
  mensaje: string;
}

export interface ImportConfirmResponse {
  imported_count: number;
  errors: ImportError[];
}

// ── Threshold ──
export interface Umbral {
  umbral_pct: number;
}

// ── Analytics ──
export interface Atrasado {
  alumno_id: string;
  nombre: string;
  email: string;
  actividades_faltantes: number;
  nota_promedio: number | null;
  estado: string;
}

export interface RankingEntry {
  alumno_id: string;
  nombre: string;
  email: string;
  actividades_aprobadas: number;
  total_actividades: number;
}

export interface ReporteRapido {
  total_alumnos: number;
  aprobados: number;
  pendientes: number;
  promocionan: number;
  libres: number;
}

export interface NotaFinal {
  alumno_id: string;
  nombre: string;
  email: string;
  nota_final: number | null;
  estado: string;
}

export interface TpsSinCorregirEntry {
  alumno_id: string;
  nombre: string;
  actividad: string;
  fecha_entrega: string;
}

// ── Monitoring ──
export interface MonitorFilters {
  nombre?: string;
  email?: string;
  actividad?: string;
  comision?: string;
  regional?: string;
  min_actividades_completadas?: number;
  fecha_desde?: string;
  fecha_hasta?: string;
}

export interface MonitorEntry {
  alumno_id: string;
  nombre: string;
  email: string;
  materia: string;
  comision: string;
  regional: string;
  estado_actividades: {
    actividad_id: string;
    nombre: string;
    aprobada: boolean;
    nota: number | null;
  }[];
}

export interface MonitorPaginatedResponse {
  data: MonitorEntry[];
  total: number;
  page: number;
  total_pages: number;
}

// ── Communications ──
export interface ComunicacionPreviewRequest {
  materia_id: string;
  alumno_ids: string[];
}

export interface ComunicacionPreview {
  asunto: string;
  cuerpo: string;
}

export interface ComunicacionEnviarRequest {
  materia_id: string;
  alumno_ids: string[];
  asunto: string;
  cuerpo: string;
}

export interface ComunicacionEnviarResponse {
  lote_id: string;
}

export interface ComunicacionItem {
  id: string;
  alumno_nombre: string;
  alumno_email: string;
  estado: string;
  error?: string;
}

export interface ComunicacionLote {
  lote_id: string;
  estado: string;
  requiere_aprobacion: boolean;
  items: ComunicacionItem[];
}

export interface LoteActionResponse {
  success: boolean;
}

export interface ClearDataResponse {
  success: boolean;
}
