import api from '@/shared/services/api';
import type {
  MonitorFilters,
  MonitorEntry,
  AuditoriaEntry,
  PaginatedResponse,
} from '../types/monitor.types';

export async function getMonitorGeneral(
  filters?: MonitorFilters,
  page = 1,
): Promise<PaginatedResponse<MonitorEntry>> {
  const { data } = await api.get<PaginatedResponse<MonitorEntry>>('/api/v1/analisis/monitor/general', {
    params: { ...filters, page },
  });
  return data;
}

export async function getAuditoria(
  filters?: MonitorFilters,
  page = 1,
): Promise<PaginatedResponse<AuditoriaEntry>> {
  const { data } = await api.get<PaginatedResponse<AuditoriaEntry>>('/api/v1/analisis/monitor/auditoria', {
    params: { ...filters, page },
  });
  return data;
}
