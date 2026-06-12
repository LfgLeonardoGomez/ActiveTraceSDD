export interface Carrera {
  id: string;
  codigo: string;
  nombre: string;
  activa: boolean;
  creada: string;
}

export interface Cohorte {
  id: string;
  nombre: string;
  year: number;
  fecha_desde: string;
  fecha_hasta: string;
  estado: string;
}

export interface Programa {
  id: string;
  materia: string;
  materia_id: string;
  carrera: string;
  cohorte: string;
  titulo: string;
  filename: string;
  fecha_subida: string;
}

export interface Evaluacion {
  id: string;
  materia: string;
  materia_id: string;
  cohorte: string;
  cohorte_id: string;
  tipo: 'parcial' | 'tp' | 'coloquio';
  instancia: number;
  fecha: string;
  titulo: string;
}
