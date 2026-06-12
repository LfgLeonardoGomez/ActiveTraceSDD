import api from '@/shared/services/api';
import type {
  LiquidacionView,
  LiquidacionHistorialEntry,
  HistorialFilters,
  Periodo,
} from '../types/liquidaciones.types';

export async function getLiquidacion(cohorteId: string, periodo: string): Promise<LiquidacionView> {
  const { data } = await api.get<LiquidacionView>(`/api/liquidaciones/${cohorteId}/${periodo}`);
  return data;
}

export async function cerrarLiquidacion(cohorteId: string, periodo: string): Promise<void> {
  await api.post(`/api/liquidaciones/${cohorteId}/${periodo}/cerrar`, { confirmado: true });
}

export async function getHistorial(filters?: HistorialFilters): Promise<{
  items: LiquidacionHistorialEntry[];
  total: number;
}> {
  const { data } = await api.get('/api/liquidaciones/historial', { params: filters });
  return data;
}

export async function getCohortes(): Promise<{ id: string; nombre: string }[]> {
  const { data } = await api.get('/api/liquidaciones/cohortes');
  return data;
}
