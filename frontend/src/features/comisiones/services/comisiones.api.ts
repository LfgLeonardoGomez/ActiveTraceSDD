import api from '@/shared/services/api';
import type {
  MateriaCohorte,
  ImportPreviewResponse,
  ImportConfirmRequest,
  ImportConfirmResponse,
  Umbral,
  Atrasado,
  RankingEntry,
  ReporteRapido,
  NotaFinal,
  TpsSinCorregirEntry,
  MonitorFilters,
  MonitorPaginatedResponse,
  ComunicacionPreviewRequest,
  ComunicacionPreview,
  ComunicacionEnviarRequest,
  ComunicacionEnviarResponse,
  ComunicacionLote,
  LoteActionResponse,
  ClearDataResponse,
} from '../types/comisiones.types';

export async function getMisComisiones(): Promise<MateriaCohorte[]> {
  const { data } = await api.get<MateriaCohorte[]>('/api/v1/calificaciones/comisiones');
  return data;
}

export async function importPreview(formData: FormData): Promise<ImportPreviewResponse> {
  const { data } = await api.post<ImportPreviewResponse>('/api/v1/calificaciones/preview', formData);
  return data;
}

export async function importConfirm(req: ImportConfirmRequest): Promise<ImportConfirmResponse> {
  const { data } = await api.post<ImportConfirmResponse>('/api/v1/calificaciones/import', req);
  return data;
}

export async function importFinalizacion(formData: FormData): Promise<{ sin_corregir: TpsSinCorregirEntry[] }> {
  const { data } = await api.post<{ sin_corregir: TpsSinCorregirEntry[] }>(
    '/api/v1/calificaciones/import-finalizacion',
    formData,
  );
  return data;
}

export async function getUmbral(materiaId: string): Promise<Umbral> {
  const { data } = await api.get<Umbral>(`/api/v1/umbral/${materiaId}`);
  return data;
}

export async function updateUmbral(materiaId: string, payload: Umbral): Promise<Umbral> {
  const { data } = await api.put<Umbral>(`/api/v1/umbral/${materiaId}`, payload);
  return data;
}

export async function getAtrasados(materiaId: string): Promise<Atrasado[]> {
  const { data } = await api.get<Atrasado[]>('/api/analisis/atrasados', {
    params: { materia_id: materiaId },
  });
  return data;
}

export async function getRanking(materiaId: string): Promise<RankingEntry[]> {
  const { data } = await api.get<RankingEntry[]>('/api/analisis/ranking', {
    params: { materia_id: materiaId },
  });
  return data;
}

export async function getReporteRapido(materiaId: string): Promise<ReporteRapido> {
  const { data } = await api.get<ReporteRapido>('/api/analisis/reporte-rapido', {
    params: { materia_id: materiaId },
  });
  return data;
}

export async function getNotasFinales(materiaId: string): Promise<NotaFinal[]> {
  const { data } = await api.get<NotaFinal[]>('/api/analisis/notas-finales', {
    params: { materia_id: materiaId },
  });
  return data;
}

export function getNotasFinalesExportUrl(materiaId: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? '';
  return `${base}/api/analisis/notas-finales/export?materia_id=${materiaId}`;
}

export async function getTpsSinCorregir(materiaId: string): Promise<TpsSinCorregirEntry[]> {
  const { data } = await api.get<TpsSinCorregirEntry[]>('/api/analisis/tps-sin-corregir', {
    params: { materia_id: materiaId },
  });
  return data;
}

export function getTpsSinCorregirExportUrl(materiaId: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? '';
  return `${base}/api/analisis/tps-sin-corregir/export?materia_id=${materiaId}`;
}

export async function getMonitor(
  materiaId: string,
  filters: MonitorFilters,
  page: number,
  esCoordinador = false,
): Promise<MonitorPaginatedResponse> {
  const endpoint = esCoordinador ? '/api/analisis/monitor/general' : '/api/analisis/monitor/propio';
  const { data } = await api.get<MonitorPaginatedResponse>(endpoint, {
    params: { materia_id: materiaId, ...filters, page },
  });
  return data;
}

export async function previewComunicacion(req: ComunicacionPreviewRequest): Promise<ComunicacionPreview> {
  const { data } = await api.post<ComunicacionPreview>('/api/comunicaciones/preview', req);
  return data;
}

export async function enviarComunicacion(req: ComunicacionEnviarRequest): Promise<ComunicacionEnviarResponse> {
  const { data } = await api.post<ComunicacionEnviarResponse>('/api/comunicaciones/lote', req);
  return data;
}

export async function getLoteStatus(loteId: string): Promise<ComunicacionLote> {
  const { data } = await api.get<ComunicacionLote>(`/api/comunicaciones/lote/${loteId}/estado`);
  return data;
}

export async function loteAction(
  loteId: string,
  action: 'approve' | 'cancel' | 'retry',
  comunicacionId?: string,
): Promise<LoteActionResponse> {
  const params = comunicacionId ? { comunicacion_id: comunicacionId } : {};
  const { data } = await api.post<LoteActionResponse>(
    `/api/comunicaciones/lote/${loteId}/${action}`,
    params,
  );
  return data;
}

export async function clearData(materiaId: string): Promise<ClearDataResponse> {
  const { data } = await api.post<ClearDataResponse>('/api/v1/calificaciones/vaciar', {
    materia_id: materiaId,
  });
  return data;
}
