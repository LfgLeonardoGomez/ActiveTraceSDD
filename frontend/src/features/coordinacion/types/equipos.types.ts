export interface Equipo {
  id: string;
  materia: string;
  materia_id: string;
  carrera: string;
  cohorte: string;
  cohorte_id: string;
  roles: string[];
  vigencia_desde: string;
  vigencia_hasta: string;
  estado: string;
}

export interface Asignacion {
  id: string;
  docente: string;
  docente_id: string;
  materia: string;
  materia_id: string;
  carrera: string;
  cohorte: string;
  cohorte_id: string;
  rol: string;
  fecha_desde: string;
  fecha_hasta: string;
  estado: string;
}

export interface AsignacionRequest {
  docente_id: string;
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
  rol: string;
  fecha_desde: string;
  fecha_hasta: string;
}

export interface AsignacionMasivaRequest extends Omit<AsignacionRequest, 'docente_id'> {
  docente_ids: string[];
}

export interface UsuarioDocente {
  id: string;
  nombre: string;
  email: string;
  rol: string;
  regional: string;
  activo: boolean;
}

export interface ClonarEquipoRequest {
  origen: { materia_id: string; cohorte_id: string };
  destino: { materia_id: string; cohorte_id: string };
}
