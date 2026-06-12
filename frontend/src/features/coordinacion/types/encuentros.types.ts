export interface Encuentro {
  id: string;
  materia: string;
  materia_id: string;
  cohorte: string;
  cohorte_id: string;
  docente: string;
  docente_id: string;
  fecha: string;
  hora: string;
  titulo?: string;
  estado: 'programado' | 'realizado' | 'cancelado';
  enlace: string | null;
  grabacion: string | null;
  comentario_interno?: string | null;
}

export interface SerieRecurrenteRequest {
  materia_id: string;
  dia_semana: 1 | 2 | 3 | 4 | 5;
  horario: string;
  fecha_inicio: string;
  semanas: number;
  titulo: string;
  enlace?: string;
}

export interface EncuentroFilters {
  materia_id?: string;
  cohorte_id?: string;
  docente_id?: string;
  estado?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  q?: string;
  page?: string;
  per_page?: string;
}

export interface Guardia {
  id: string;
  tutor: string;
  tutor_id: string;
  materia: string;
  materia_id: string;
  carrera: string;
  cohorte: string;
  dia: string;
  horario_desde: string;
  horario_hasta: string;
  estado: string;
  comentarios: string | null;
}

export interface GuardiaFilters {
  tutor_id?: string;
  materia_id?: string;
  estado?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  page?: string;
  per_page?: string;
}
