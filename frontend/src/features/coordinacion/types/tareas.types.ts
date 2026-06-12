export type TareaEstado = 'pendiente' | 'en_proceso' | 'completada' | 'aprobada' | 'rechazada';

export interface TareaComment {
  id: string;
  autor: string;
  contenido: string;
  fecha: string;
}

export interface Tarea {
  id: string;
  titulo: string;
  descripcion: string;
  asignado: string;
  asignado_id: string;
  asignador: string;
  asignador_id: string;
  materia: string | null;
  estado: TareaEstado;
  prioridad: string;
  fecha_creacion: string;
  fecha_limite: string | null;
  comentarios: TareaComment[];
}

export interface TareaFilters {
  estado?: TareaEstado;
  materia?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  q?: string;
}
