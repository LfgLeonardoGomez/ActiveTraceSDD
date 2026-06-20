import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type { Aviso, AvisoFormData } from '../types/avisos.types';

// Raw shape returned by GET /api/avisos/ (AvisoResponseSchema)
interface AvisoApiItem {
  id: string;
  tenant_id: string;
  alcance: string;
  materia_id: string | null;
  cohorte_id: string | null;
  rol_destino: string | null;
  severidad: string;
  titulo: string;
  cuerpo: string;
  inicio_en: string;
  fin_en: string;
  orden: number;
  activo: boolean;
  requiere_ack: boolean;
  created_at: string;
  updated_at: string;
}

function mapAvisoApiToView(item: AvisoApiItem): Aviso {
  return {
    id: item.id,
    titulo: item.titulo,
    cuerpo: item.cuerpo,
    alcance: item.alcance as Aviso['alcance'],
    materia_id: item.materia_id,
    cohorte_id: item.cohorte_id,
    roles_destinatarios: item.rol_destino ? [item.rol_destino] : [],
    severidad: item.severidad as Aviso['severidad'],
    estado: item.activo ? 'publicado' : 'borrador',
    fecha_desde: item.inicio_en,
    fecha_hasta: item.fin_en,
    requiere_ack: item.requiere_ack,
    creado: item.created_at,
    total_destinatarios: 0,
    leidos: 0,
  };
}

export async function getAvisos(filters?: Record<string, string>): Promise<Aviso[]> {
  const { data } = await api.get<AvisoApiItem[] | Paginated<AvisoApiItem>>('/api/avisos/', { params: filters });
  return toList(data).map(mapAvisoApiToView);
}

export async function crearAviso(payload: AvisoFormData): Promise<Aviso> {
  const { data } = await api.post<AvisoApiItem>('/api/avisos/', payload);
  return mapAvisoApiToView(data);
}

export async function editarAviso(id: string, payload: Partial<AvisoFormData>): Promise<Aviso> {
  const { data } = await api.put<AvisoApiItem>(`/api/avisos/${id}`, payload);
  return mapAvisoApiToView(data);
}

export async function eliminarAviso(id: string): Promise<void> {
  await api.delete(`/api/avisos/${id}`);
}

export async function confirmarAck(id: string): Promise<void> {
  await api.post(`/api/avisos/${id}/confirmar`);
}
