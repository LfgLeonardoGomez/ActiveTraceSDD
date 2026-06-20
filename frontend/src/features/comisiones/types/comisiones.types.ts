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
  entrada_padron_id: string;
  alumno_nombre: string;
  alumno_email: string;
  motivo: string;
  actividades_faltantes_count: number;
  actividades_reprobadas_count: number;
}

export interface RankingEntry {
  posicion: number;
  entrada_padron_id: string;
  alumno_nombre: string;
  actividades_aprobadas: number;
}

export interface ReporteRapido {
  total_alumnos: number;
  total_actividades: number;
  con_aprobadas: number;
  atrasados: number;
  pct_aprobacion: number;
  sin_datos: boolean;
}

export interface NotaFinal {
  entrada_padron_id: string;
  alumno_nombre: string;
  alumno_email: string;
  nota_final: number | null;
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
  entrada_padron_id: string;
  alumno_nombre: string;
  email: string;
  materia_id: string;
  materia_nombre: string;
  actividades_aprobadas: number;
  actividades_totales: number;
  estado: string;
}

export interface MonitorPaginatedResponse {
  items: MonitorEntry[];
  total: number;
  page: number;
  pages: number;
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
