export interface Aviso {
  id: string;
  titulo: string;
  cuerpo: string;
  alcance: 'global' | 'materia' | 'cohorte';
  materia_id: string | null;
  cohorte_id: string | null;
  roles_destinatarios: string[];
  severidad: 'informativo' | 'advertencia' | 'critico';
  estado: string;
  fecha_desde: string | null;
  fecha_hasta: string | null;
  requiere_ack: boolean;
  creado: string;
  total_destinatarios: number;
  leidos: number;
}

export interface AvisoFormData {
  titulo: string;
  cuerpo: string;
  alcance: 'global' | 'materia' | 'cohorte';
  materia_id?: string;
  cohorte_id?: string;
  roles_destinatarios: string[];
  severidad: 'informativo' | 'advertencia' | 'critico';
  estado?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  requiere_ack: boolean;
}

export interface AckEntry {
  destinatario: string;
  rol: string;
  leido: boolean;
  fecha_lectura: string | null;
}
