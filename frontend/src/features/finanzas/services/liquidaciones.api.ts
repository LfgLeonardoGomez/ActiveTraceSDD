import api from '@/shared/services/api';
import { toList, type Paginated } from '@/shared/services/pagination';
import type {
  LiquidacionView,
  LiquidacionHistorialEntry,
  HistorialFilters,
} from '../types/liquidaciones.types';

// GET /api/v1/liquidaciones/{cohorte_id}/{periodo}
export async function getLiquidacion(cohorteId: string, periodo: string): Promise<LiquidacionView> {
  const { data } = await api.get<LiquidacionView>(`/api/v1/liquidaciones/${cohorteId}/${periodo}`);
  return data;
}

// POST /api/v1/liquidaciones/{cohorte_id}/{periodo}/cerrar
// Body: CerrarLiquidacionRequest — confirmar_cierre (bool, must be true) + periodo (must match URL)
export async function cerrarLiquidacion(cohorteId: string, periodo: string): Promise<LiquidacionView> {
  const { data } = await api.post<LiquidacionView>(
    `/api/v1/liquidaciones/${cohorteId}/${periodo}/cerrar`,
    { confirmar_cierre: true, periodo },
  );
  return data;
}

// GET /api/v1/liquidaciones/historial — returns HistorialResponse { items, total, page, page_size }
export async function getHistorial(filters?: HistorialFilters): Promise<{
  items: LiquidacionHistorialEntry[];
  total: number;
  page: number;
  page_size: number;
}> {
  const { data } = await api.get('/api/v1/liquidaciones/historial', { params: filters });
  return data;
}

// GET /api/v1/liquidaciones/{cohorte_id}/{periodo}/exportar
export async function exportarLiquidacion(cohorteId: string, periodo: string): Promise<LiquidacionView> {
  const { data } = await api.get<LiquidacionView>(`/api/v1/liquidaciones/${cohorteId}/${periodo}/exportar`);
  return data;
}

// NOTE: /api/v1/liquidaciones/cohortes does NOT exist. Cohortes are managed by the
// comisiones/estructura-academica module. Remove the non-existent getCohortes function.
// If a cohortes list is needed, wire it to the correct module endpoint when available.
export async function getMateriaGrupoPlus(filters?: Record<string, unknown>): Promise<{ id: string; materia_id: string; grupo: string; desde: string; hasta: string | null }[]> {
  const { data } = await api.get<{ id: string; materia_id: string; grupo: string; desde: string; hasta: string | null }[] | Paginated<{ id: string; materia_id: string; grupo: string; desde: string; hasta: string | null }>>('/api/v1/liquidaciones/materia-grupo-plus', { params: filters });
  return toList(data);
}
