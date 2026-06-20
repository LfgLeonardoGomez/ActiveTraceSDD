export interface MetricasColoquios {
  total_alumnos_cargados: number;
  instancias_activas: number;
  reservas_activas: number;
  notas_registradas: number;
}

export interface ConvocatoriaDia {
  fecha: string;
  cupo_maximo: number;
}

export interface Convocatoria {
  id: string;
  materia: string;
  materia_id: string;
  /** Free-text instance label returned by the API (e.g. "Primer Coloquio 2026"). */
  instancia: string;
  titulo: string;
  cohorte: string;
  cohorte_id: string;
  dias: ConvocatoriaDia[];
  /** Total number of available days as reported by the API (dias_disponibles). */
  dias_disponibles: number;
  estado: string;
  total_convocados: number;
  reservas_activas: number;
  cupos_libres: number;
}

export interface ImportResult {
  imported_count: number;
  errors: Array<{ row: number; mensaje: string; legajo?: string }>;
}

export interface Reserva {
  id: string;
  alumno: string;
  alumno_id: string;
  convocatoria_id: string;
  dia: string;
  horario: string;
  estado: string;
}
